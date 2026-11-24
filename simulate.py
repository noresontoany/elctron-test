#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.28,<1"]
# ///
"""Live workshop traffic. Run: uv run simulate.py --help (no database access)."""

import argparse
import asyncio
import fcntl
import json
import logging
import math
import os
import random
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, uuid4, uuid5

import httpx

ROOT = Path(__file__).resolve().parent
STATE = ROOT / ".artifacts" / "simulator"
LOG = logging.getLogger("spoke-simulator")
JOBS = [
    ("Настройка переключателя", 1800),
    ("Замена цепи", 2200),
    ("Прокачка тормозов", 3200),
    ("Полное ТО велосипеда", 6500),
    ("Замена покрышек", 2400),
    ("Выправить восьмёрку", 1500),
    ("Переборка каретки", 2800),
    ("Установка крыльев", 900),
]
BIKES = [
    "Trek Marlin 7",
    "Giant Escape 2",
    "Cube Aim Pro",
    "Scott Aspect 950",
    "Merida Big Nine",
]
CUSTOMERS = ["Анна", "Михаил", "Дмитрий", "Елена", "Иван", "Ольга", "София", "Павел"]


def positive_rate(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError(
            "Темп должен быть положительным конечным числом"
        )
    return number


def duration(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise argparse.ArgumentTypeError(
            "Длительность должна быть >= 0 (0 — до остановки)"
        )
    return number


class Simulator:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.run_id = (
            datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:6]
        )
        self.rows: dict[str, dict] = {}
        self.created_ids: set[str] = set()
        self.created = 0
        self.operator_token = ""
        self.processed = 0
        self.failures = 0
        self.ready = asyncio.Event()
        self.journal = STATE / f"{self.run_id}.jsonl"
        self.client = httpx.AsyncClient(base_url=args.url.rstrip("/"), timeout=65)

    def record(self, event: str, **fields) -> None:
        with self.journal.open("a") as stream:
            stream.write(
                json.dumps(
                    {"time": datetime.now(UTC).isoformat(), "event": event, **fields},
                    ensure_ascii=False,
                )
                + "\n"
            )

    async def sync_orders(self) -> None:
        """Materialize the Electric shape, including snapshot chunks and later changes."""
        offset, handle = "-1", None
        while True:
            try:
                params = {"offset": offset}
                if handle:
                    params["handle"] = handle
                if self.ready.is_set():
                    params["live"] = "true"
                response = await self.client.get("/api/sync/orders", params=params)
                if response.status_code == 409:
                    self.rows.clear()
                    self.ready.clear()
                    offset, handle = "-1", None
                    continue
                response.raise_for_status()
                reset = False
                if response.status_code != 204:
                    for message in response.json():
                        headers = message.get("headers", {})
                        control = headers.get("control")
                        if control == "must-refetch":
                            reset = True
                            break
                        if control == "up-to-date":
                            self.ready.set()
                        value = message.get("value", {})
                        order_id = value.get("id")
                        if headers.get("operation") == "delete":
                            self.rows.pop(order_id, None)
                        elif order_id:
                            self.rows[order_id] = {
                                **self.rows.get(order_id, {}),
                                **value,
                            }
                if reset:
                    self.rows.clear()
                    self.ready.clear()
                    offset, handle = "-1", None
                    continue
                offset = response.headers.get("electric-offset", offset)
                handle = response.headers.get("electric-handle", handle)
            except httpx.HTTPError as error:
                self.ready.clear()
                LOG.warning("Electric недоступен, повтор через 3 с: %s", error)
                await asyncio.sleep(3)

    async def produce(self) -> None:
        interval = 60 / self.args.incoming
        while True:
            await asyncio.sleep(interval)
            order_id = str(uuid4())
            title, estimate = random.choice(JOBS)
            body = {
                "id": order_id,
                "title": title,
                "bike": random.choice(BIKES),
                "customer_name": f"Демо · {random.choice(CUSTOMERS)}",
                "description": f"Симуляция {self.run_id}. Клиент оставил велосипед на проверку.",
                "estimate": estimate,
                "priority": random.choice(["normal"] * 4 + ["urgent"]),
            }
            # Record the exact UUID before sending: an interrupted reply may still commit.
            self.created_ids.add(order_id)
            self.record("create_attempt", id=order_id)
            try:
                response = await self.client.post("/api/orders", json=body, timeout=15)
                response.raise_for_status()
                self.created += 1
                self.record("created", id=order_id, txid=response.json()["txid"])
                LOG.info(
                    "+ Заказ %-8s %-30s | поступило: %s",
                    order_id[:8],
                    title,
                    self.created,
                )
            except httpx.HTTPError as error:
                self.failures += 1
                LOG.warning(
                    "Создание не подтверждено (без автоматического повтора): %s", error
                )

    async def operate(self) -> None:
        interval = 60 / self.args.operator
        while True:
            await asyncio.sleep(interval)
            if not self.ready.is_set():
                LOG.info("Оператор ждёт синхронизации")
                continue
            candidates = [
                row
                for key, row in self.rows.items()
                if key in self.created_ids and row.get("status") == "queued"
            ]
            if not candidates:
                LOG.info("Оператор: очередь этого запуска пуста")
                continue
            order = min(candidates, key=lambda row: (row["created_at"], row["id"]))
            try:
                response = await self.client.post(
                    f"/api/orders/{order['id']}/claim",
                    headers={"Authorization": f"Bearer {self.operator_token}"},
                    json={
                        "version": int(order["version"]),
                    },
                    timeout=15,
                )
                if response.status_code in (404, 409):
                    LOG.info(
                        "Заказ уже изменился: %s; ждём следующий такт", order["id"][:8]
                    )
                    continue
                response.raise_for_status()
                self.processed += 1
                self.record("processed", id=order["id"], txid=response.json()["txid"])
                LOG.info(
                    "→ Проверен %-8s → В работе | проверено: %s | очередь: ~%s",
                    order["id"][:8],
                    self.processed,
                    len(candidates) - 1,
                )
                # Do not patch self.rows: confirmation must arrive through Electric.
            except httpx.HTTPError as error:
                self.failures += 1
                LOG.warning("Оператор не смог обработать заказ: %s", error)

    async def run(self) -> None:
        stop = asyncio.Event()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop.set)
        async with self.client:
            response = await self.client.post(
                "/api/session", json={"workspace": self.args.workspace}
            )
            response.raise_for_status()
            manager_token = response.json()["token"]
            self.client.headers["Authorization"] = f"Bearer {manager_token}"
            operator_id = uuid5(NAMESPACE_URL, f"spoke/{self.args.workspace}/user/Алексей")
            operator_session = await self.client.post(
                "/api/session", json={"workspace": self.args.workspace, "user_id": str(operator_id)}
            )
            operator_session.raise_for_status()
            self.operator_token = operator_session.json()["token"]
            self.record(
                "started",
                run_id=self.run_id,
                incoming=self.args.incoming,
                operator=self.args.operator,
                workspace=self.args.workspace,
            )
            LOG.info(
                "%s | вход: %g/мин | оператор: %g/мин | длительность: %s",
                self.args.url,
                self.args.incoming,
                self.args.operator,
                f"{self.args.duration:g} мин" if self.args.duration else "до остановки",
            )
            LOG.info(
                "Оператор берёт только заказы этого запуска. Журнал: %s", self.journal
            )
            tasks = [
                asyncio.create_task(self.sync_orders()),
                asyncio.create_task(self.produce()),
                asyncio.create_task(self.operate()),
            ]
            try:
                # Any unexpected worker failure stops the run instead of leaving half a simulator.
                for task in tasks:
                    task.add_done_callback(
                        lambda task: stop.set() if not task.cancelled() else None
                    )
                if self.args.duration:
                    try:
                        await asyncio.wait_for(
                            stop.wait(), timeout=self.args.duration * 60
                        )
                    except TimeoutError:
                        pass
                else:
                    await stop.wait()
            finally:
                for task in tasks:
                    task.cancel()
                results = await asyncio.gather(*tasks, return_exceptions=True)
                errors = [
                    result
                    for result in results
                    if isinstance(result, Exception)
                    and not isinstance(result, asyncio.CancelledError)
                ]
                self.record(
                    "stopped",
                    created=self.created,
                    processed=self.processed,
                    failures=self.failures + len(errors),
                )
                LOG.info(
                    "Остановлено. Создано: %s; проверено: %s; ошибки запросов: %s",
                    self.created,
                    self.processed,
                    self.failures,
                )
                if errors:
                    raise errors[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8097", help="Адрес проекта")
    parser.add_argument(
        "--incoming", type=positive_rate, default=10, help="Заказов в минуту (10)"
    )
    parser.add_argument(
        "--operator", type=positive_rate, default=5, help="Проверок в минуту (5)"
    )
    parser.add_argument(
        "--duration",
        type=duration,
        default=10,
        help="Минуты работы (10); 0 — без лимита",
    )
    parser.add_argument("--workspace", choices=["studio", "lab"], default="studio")
    parser.add_argument(
        "--stop", action="store_true", help="Остановить работающий симулятор"
    )
    parser.add_argument("--background", action="store_true", help="Запустить в фоне")
    args = parser.parse_args()
    STATE.mkdir(parents=True, exist_ok=True)
    pid_path = STATE / "running.json"
    if args.background and not args.stop:
        with (STATE / "run.lock").open("w") as guard:
            try:
                fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                parser.error("Симулятор уже запущен. Сначала выполните --stop")
        log_path = STATE.parent / "simulator.log"
        with log_path.open("a") as output:
            child = subprocess.Popen(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    *[arg for arg in sys.argv[1:] if arg != "--background"],
                ],
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=output,
                cwd=ROOT,
                start_new_session=True,
            )
        for _ in range(30):
            if child.poll() is not None:
                parser.error(f"Симулятор не запустился. См. {log_path}")
            if (
                pid_path.exists()
                and json.loads(pid_path.read_text())["pid"] == child.pid
            ):
                print(f"Симулятор запущен в фоне: PID {child.pid}. Лог: {log_path}")
                return
            time.sleep(0.1)
        parser.error(f"Проверьте запуск по логу: {log_path}")
    if args.stop:
        if not pid_path.exists():
            print("Симулятор уже остановлен")
            return
        state = json.loads(pid_path.read_text())
        pid = state["pid"]
        try:
            # Linux process start time prevents signaling an unrelated process after PID reuse.
            start = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
            if start != state["start"]:
                raise ProcessLookupError
            os.kill(pid, signal.SIGTERM)
            print(f"Остановка симулятора, PID {pid}")
        except (ProcessLookupError, FileNotFoundError):
            print("Симулятор уже остановлен")
        return
    with (STATE / "run.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error("Симулятор уже запущен. Сначала выполните --stop")
        start = (
            Path(f"/proc/{os.getpid()}/stat").read_text().rsplit(")", 1)[1].split()[19]
        )
        pid_path.write_text(
            json.dumps({"pid": os.getpid(), "start": start, "time": time.time()})
        )
        try:
            asyncio.run(Simulator(args).run())
        finally:
            pid_path.unlink(missing_ok=True)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S"
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    main()
