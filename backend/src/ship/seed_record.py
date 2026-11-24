from sqlalchemy import Text
from sqlalchemy.orm import Mapped, mapped_column

from src.ship.base import Base


class SeedRecord(Base):
    __tablename__ = "demo_seeds"
    name: Mapped[str] = mapped_column(Text, primary_key=True)
