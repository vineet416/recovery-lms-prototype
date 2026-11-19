from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# One person who can log in (caller, manager, head, coo or customer service).
class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    role: Mapped[str]
    office_id: Mapped[int] = mapped_column(ForeignKey("office.id"))
    manager_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    username: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]
