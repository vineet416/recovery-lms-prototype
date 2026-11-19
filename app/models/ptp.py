from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# One promise to pay: how much and by when. State is Pending, Kept or Broken.
class Ptp(Base):
    __tablename__ = "ptp"
    __table_args__ = (Index("ix_ptp_state_promise_date", "state", "promise_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    promise_date: Mapped[date]
    state: Mapped[str] = mapped_column(default="Pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
