"""Seed a new installation once; never resurrect deleted demo orders on restart."""

import asyncio
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert

from src.containers.order.models.order import Order
from src.containers.team.models.directory import Team, TeamMember, User  # noqa: F401
from src.ship.database import engine, session_factory
from src.ship.demo_ids import demo_id

ROWS = [
    (
        "Полное ТО перед сезоном",
        "Trek Marlin 7",
        "Анна Смирнова",
        "queued",
        "urgent",
        "Алексей",
        6500,
        "Проверить трансмиссию, прокачать тормоза и заменить тросики.",
    ),
    (
        "Настройка переключателя",
        "Giant Escape 2",
        "Михаил Орлов",
        "queued",
        "normal",
        "Не назначен",
        1800,
        "Цепь перескакивает на больших звёздах. Проверить петух.",
    ),
    (
        "Замена покрышек",
        "Cube Aim Pro",
        "Дмитрий Волков",
        "queued",
        "normal",
        "Мария",
        2400,
        "Поставить Schwalbe Smart Sam 29 × 2.25. Покрышки у клиента.",
    ),
    (
        "Прокачка тормозов",
        "Specialized Rockhopper",
        "Елена Ким",
        "repair",
        "urgent",
        "Алексей",
        3200,
        "Задний тормоз проваливается. Проверить герметичность системы.",
    ),
    (
        "Переборка втулки",
        "Merida Big Nine",
        "Иван Петров",
        "repair",
        "normal",
        "Мария",
        2800,
        "Люфт заднего колеса, заменить подшипники и смазку.",
    ),
    (
        "Обновление трансмиссии",
        "Scott Aspect 950",
        "Ольга Белова",
        "repair",
        "normal",
        "Алексей",
        8900,
        "Новая цепь и кассета 11–42. Детали уже на складе.",
    ),
    (
        "Восьмёрка на колесе",
        "Cannondale Trail 5",
        "Павел Соколов",
        "ready",
        "normal",
        "Мария",
        1500,
        "Колесо выправлено, натяжение спиц проверено. Готов к выдаче.",
    ),
    (
        "Установка аксессуаров",
        "Electra Loft 7D",
        "София Морозова",
        "ready",
        "normal",
        "Алексей",
        1200,
        "Крылья, багажник и передний фонарь установлены.",
    ),
    (
        "Замена тормозных колодок",
        "Author Solution",
        "Артём Ли",
        "delivered",
        "normal",
        "Мария",
        1600,
        "Велосипед выдан владельцу. Хороших поездок!",
    ),
]


async def main():
    async with session_factory() as session, session.begin():
        # Separate seed marker: an empty board must stay empty after restart.
        result = await session.execute(
            text(
                "INSERT INTO demo_seeds (name) VALUES ('initial-v1') "
                "ON CONFLICT DO NOTHING RETURNING name"
            )
        )
        if result.scalar_one_or_none() is None:
            return
        for i, row in enumerate(ROWS):
            title, bike, customer, status, priority, assignee, estimate, description = row
            await session.execute(
                insert(Order).values(
                    id=uuid5(NAMESPACE_URL, f"spoke/studio/{i}"),
                    workspace_id="studio",
                    title=title,
                    bike=bike,
                    customer_name=customer,
                    status=status,
                    priority=priority,
                    assignee_id=demo_id("studio", "user", assignee)
                    if assignee != "Не назначен"
                    else None,
                    team_id=demo_id(
                        "studio", "team", "wheels" if assignee == "Мария" else "service"
                    ),
                    estimate=estimate,
                    description=description,
                    version=1,
                )
            )
        await session.execute(
            insert(Order).values(
                id=uuid5(NAMESPACE_URL, "spoke/lab/0"),
                workspace_id="lab",
                title="Диагностика электровелосипеда",
                bike="Specialized Turbo Vado",
                customer_name="Никита Зайцев",
                description="Проверить батарею и датчик каденса.",
                status="queued",
                priority="normal",
                assignee_id=None,
                team_id=demo_id("lab", "team", "service"),
                estimate=3000,
                version=1,
            )
        )
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
