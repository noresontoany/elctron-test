from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.ship.workspace import Workspace


class DemoSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: UUID | None = None
    workspace: Workspace = Workspace.STUDIO
