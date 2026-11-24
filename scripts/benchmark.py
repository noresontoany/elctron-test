#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx[http2]>=0.28,<1"]
# ///
"""Bounded open-loop benchmark of your own Spoke instance; no DB credentials needed."""

import argparse
import asyncio
import json
import math
import ssl
import time
from collections import Counter
from contextlib import AsyncExitStack
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import httpx


def positive(value):
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise argparse.ArgumentTypeError("Ожидается положительное конечное число")
    return result


def count(value):
    result = int(value)
    if result < 1:
        raise argparse.ArgumentTypeError("Ожидается целое >= 1")
    return result


def distribution(values):
    ordered = sorted(values)
    if not ordered:
        return {"count": 0}
    return {
        "count": len(ordered),
        **{
            f"p{p}_ms": round(
                ordered[min(len(ordered) - 1, math.ceil(p / 100 * len(ordered)) - 1)]
                * 1000,
                2,
            )
            for p in (50, 95, 99)
        },
        "max_ms": round(ordered[-1] * 1000, 2),
    }


class Benchmark:
    def __init__(self, args):
        self.args = args
        self.run_id = (
            datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:6]
        )
        self.errors = Counter()
        self.http_versions = Counter()
        self.writes = {}
        self.api_times = []
        self.poll_times = []
        self.boot_times = []
        self.pending = set()
        self.ready = [asyncio.Event() for _ in range(args.readers * 4)]
        self.offered = self.dropped = self.polls = self.resets = 0
        self.loop_lag = []
        self.path = Path(args.output or f".artifacts/bench/{self.run_id}.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.journal = self.path.with_suffix(".ids.jsonl")
        self.journal.touch(exist_ok=False)

    async def reader(self, client, number, resource, ready):
        offset, handle, live = "-1", None, False
        buffered = []
        boot = time.perf_counter()
        while True:
            params = {"offset": offset}
            if handle:
                params["handle"] = handle
            if live:
                params["live"] = "true"
            try:
                started = time.perf_counter()
                response = await client.get(
                    f"/api/sync/{resource}", params=params, timeout=70
                )
                self.http_versions[response.http_version] += 1
                self.polls += 1
                self.poll_times.append(time.perf_counter() - started)
                if response.status_code == 409:
                    self.resets += 1
                    offset, handle, live, buffered = "-1", None, False, []
                    continue
                response.raise_for_status()
                messages = [] if response.status_code == 204 else response.json()
                reset = False
                for message in messages:
                    headers = message.get("headers", {})
                    if headers.get("control") == "must-refetch":
                        reset = True
                        break
                    if headers.get("operation") == "insert" and resource == "orders":
                        order_id = message.get("value", {}).get("id")
                        if order_id in self.writes:
                            buffered.append((order_id, headers.get("txids", [])))
                    if headers.get("control") == "up-to-date":
                        now = time.perf_counter()
                        for order_id, txids in buffered:
                            self.writes[order_id]["observed"].setdefault(
                                number, (now, txids)
                            )
                        buffered.clear()
                        live = True
                        if not ready.is_set():
                            self.boot_times.append(now - boot)
                            ready.set()
                if reset:
                    self.resets += 1
                    offset, handle, live, buffered = "-1", None, False, []
                else:
                    offset = response.headers.get("electric-offset", offset)
                    handle = response.headers.get("electric-handle", handle)
            except (httpx.HTTPError, ValueError) as error:
                status = (
                    error.response.status_code
                    if isinstance(error, httpx.HTTPStatusError)
                    else type(error).__name__
                )
                self.errors[f"sync:{status}"] += 1
                await asyncio.sleep(1)

    async def write(self, client):
        order_id = str(uuid4())
        row = {"start": time.perf_counter(), "observed": {}, "txid": None}
        self.writes[order_id] = row
        # Journal before sending: a timed-out request can still commit.
        with self.journal.open("a") as stream:
            stream.write(json.dumps({"id": order_id, "run_id": self.run_id}) + "\n")
        try:
            response = await client.post(
                "/api/orders",
                json={
                    "id": order_id,
                    "title": f"Benchmark {self.run_id}",
                    "bike": "Load Test",
                    "customer_name": f"Bench {self.run_id}",
                    "description": f"benchmark:{self.run_id}",
                    "estimate": 100,
                },
                timeout=self.args.timeout,
            )
            self.http_versions[response.http_version] += 1
            response.raise_for_status()
            row["api_end"] = time.perf_counter()
            row["txid"] = response.json()["txid"]
            self.api_times.append(row["api_end"] - row["start"])
            if self.args.mode == "e2e":
                deadline = time.perf_counter() + self.args.timeout

                def confirmed():
                    return sum(
                        row["txid"] in txids for _, txids in row["observed"].values()
                    )

                while (
                    confirmed() < self.args.readers and time.perf_counter() < deadline
                ):
                    await asyncio.sleep(0.01)
                missing = self.args.readers - confirmed()
                if missing:
                    # Later arrivals during other writes' drain must not erase this timeout.
                    self.errors["delivery:timeout"] += missing
        except httpx.HTTPError as error:
            status = (
                error.response.status_code
                if isinstance(error, httpx.HTTPStatusError)
                else type(error).__name__
            )
            self.errors[f"write:{status}"] += 1

    async def cleanup(self, client):
        # Only our freshly generated UUIDs; version=1 protects orders someone has edited.
        for order_id in self.writes:
            try:
                response = await client.request(
                    "DELETE", f"/api/orders/{order_id}", json={"version": 1}, timeout=15
                )
                if response.status_code not in (200, 404):
                    self.errors[f"cleanup:{response.status_code}"] += 1
            except httpx.HTTPError:
                self.errors["cleanup:network"] += 1

    async def run(self):
        args = self.args
        verify = ssl.create_default_context(cafile=args.ca) if args.ca else True
        limits = httpx.Limits(
            max_connections=args.max_inflight + 8,
            max_keepalive_connections=args.max_inflight + 8,
        )
        readers = []
        started = time.perf_counter()
        try:
            async with (
                AsyncExitStack() as stack,
                httpx.AsyncClient(
                    base_url=args.url.rstrip("/"),
                    http2=args.http_version == "2",
                    verify=verify,
                    limits=limits,
                ) as client,
            ):
                response = await client.post(
                    "/api/session", json={"workspace": "lab"}, timeout=15
                )
                response.raise_for_status()
                client.headers["Authorization"] = "Bearer " + response.json()["token"]
                if args.mode != "api":
                    for number in range(args.readers):
                        # A device owns its transport. One global HTTP/2 connection would
                        # benchmark httpx stream contention instead of independent clients.
                        reader_client = await stack.enter_async_context(
                            httpx.AsyncClient(
                                base_url=args.url.rstrip("/"),
                                http2=args.http_version == "2",
                                verify=verify,
                                headers={
                                    "Authorization": client.headers["Authorization"]
                                },
                                limits=httpx.Limits(
                                    max_connections=4, max_keepalive_connections=4
                                ),
                            )
                        )
                        for index, resource in enumerate(
                            ("orders", "users", "teams", "team_members")
                        ):
                            readers.append(
                                asyncio.create_task(
                                    self.reader(
                                        reader_client,
                                        number,
                                        resource,
                                        self.ready[number * 4 + index],
                                    )
                                )
                            )
                    await asyncio.wait_for(
                        asyncio.gather(*(event.wait() for event in self.ready)),
                        args.startup_timeout,
                    )
                started = time.perf_counter()
                deadline = started + args.duration
                print(
                    f"run={self.run_id} mode={args.mode} readers={args.readers if readers else 0} rate={args.rate}/s duration={args.duration}s",
                    flush=True,
                )
                if args.mode == "sync":
                    await asyncio.sleep(args.duration)
                else:
                    # Fixed arrival schedule. Slow responses do not silently lower offered RPS.
                    sequence = 0
                    while started + sequence / args.rate < deadline:
                        scheduled = started + sequence / args.rate
                        await asyncio.sleep(max(0, scheduled - time.perf_counter()))
                        self.loop_lag.append(max(0, time.perf_counter() - scheduled))
                        self.offered += 1
                        if len(self.pending) >= args.max_inflight:
                            self.dropped += 1
                        else:
                            task = asyncio.create_task(self.write(client))
                            self.pending.add(task)
                            task.add_done_callback(self.pending.discard)
                        sequence += 1
                    await asyncio.gather(*self.pending)
                measured_end = time.perf_counter()
                for task in readers:
                    task.cancel()
                await asyncio.gather(*readers, return_exceptions=True)
                if not args.keep:
                    await self.cleanup(client)
        except (TimeoutError, httpx.HTTPError) as error:
            self.errors[f"run:{type(error).__name__}"] += 1
            measured_end = time.perf_counter()
        finally:
            for task in [*readers, *self.pending]:
                task.cancel()
            await asyncio.gather(*readers, *self.pending, return_exceptions=True)
        deliveries, after_ack, first, slowest = [], [], [], []
        for row in self.writes.values():
            if row["txid"] is None:
                continue
            times = [
                at for at, txids in row["observed"].values() if row["txid"] in txids
            ]
            deliveries.extend(at - row["start"] for at in times)
            # Delivery can beat the REST response; preserve negative values.
            after_ack.extend(at - row["api_end"] for at in times)
            if times:
                first.append(min(times) - row["start"])
            if len(times) == args.readers:
                slowest.append(max(times) - row["start"])
        expected = len(self.api_times) * args.readers if args.mode == "e2e" else 0
        report = {
            "run_id": self.run_id,
            "url": args.url,
            "mode": args.mode,
            "readers": args.readers if args.mode != "api" else 0,
            "subscriptions": args.readers * 4 if args.mode != "api" else 0,
            "duration_s": args.duration,
            "elapsed_with_drain_s": round(measured_end - started, 3),
            "offered_rps": args.rate if args.mode != "sync" else 0,
            "offered": self.offered,
            "sent": len(self.writes),
            "generator_dropped": self.dropped,
            "write_success": len(self.api_times),
            "completed_rps_including_drain": round(
                len(self.api_times) / max(0.001, measured_end - started), 3
            ),
            "write_api": distribution(self.api_times),
            "delivery_expected": expected,
            "delivery_confirmed": len(deliveries),
            "delivery_missing": expected - len(deliveries),
            "write_to_sync": distribution(deliveries),
            "api_ack_to_sync": distribution(after_ack),
            "write_to_first_reader": distribution(first),
            "write_to_all_readers": distribution(slowest),
            "initial_sync": distribution(self.boot_times),
            "poll_including_idle": distribution(self.poll_times),
            "generator_schedule_lag": distribution(self.loop_lag),
            "polls": self.polls,
            "shape_resets": self.resets,
            "http_versions": dict(self.http_versions),
            "transport_note": "Experimental httpx HTTP/2: long polls may delay other streams; compare browser benchmark"
            if args.http_version == "2"
            else "Independent HTTP/1.1 transports; browser HTTP/2 measured separately",
            "errors": dict(self.errors),
            "records_kept": args.keep,
            "ids_journal": str(self.journal),
        }
        self.path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        print(f"Отчёт: {self.path}", flush=True)
        return int(bool(self.errors or self.dropped or expected != len(deliveries)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8097")
    parser.add_argument("--mode", choices=("api", "sync", "e2e"), default="e2e")
    parser.add_argument(
        "--readers", type=count, default=4, help="Independent devices; 4 shapes each"
    )
    parser.add_argument(
        "--rate", type=positive, default=2, help="Order creates per second"
    )
    parser.add_argument(
        "--duration", type=positive, default=30, help="Seconds of offered load"
    )
    parser.add_argument("--max-inflight", type=count, default=32)
    parser.add_argument("--timeout", type=positive, default=15)
    parser.add_argument("--startup-timeout", type=positive, default=45)
    parser.add_argument("--http-version", choices=("1", "2"), default="1")
    parser.add_argument("--ca", help="Path to trusted CA PEM (local Caddy)")
    parser.add_argument("--output")
    parser.add_argument(
        "--keep", action="store_true", help="Keep this run’s orders for dataset growth"
    )
    return asyncio.run(Benchmark(parser.parse_args()).run())


if __name__ == "__main__":
    raise SystemExit(main())
