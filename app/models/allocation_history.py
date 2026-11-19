from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# One row each time an account is given or moved to a caller.
class AllocationHistory(Base):
    __tablename__ = "allocation_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"), index=True)
    from_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    to_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
