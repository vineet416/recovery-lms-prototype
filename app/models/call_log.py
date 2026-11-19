from datetime import date, datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# One phone call a caller made on an account.
class CallLog(Base):
    __tablename__ = "call_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    disposition: Mapped[str]
    remarks: Mapped[str | None]
    next_followup: Mapped[date | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
