from dataclasses import dataclass
import uuid
from datetime import datetime

@dataclass(frozen=True, slots=True)
class User:
    id: uuid.UUID
    email: str
    hashed_password: str
    is_active: bool
    created_at: datetime