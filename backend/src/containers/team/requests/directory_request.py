from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RenameUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=2, max_length=60)
    version: int = Field(ge=1, strict=True)


class AddMemberRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: UUID
    role: Literal["lead", "mechanic"] = "mechanic"
