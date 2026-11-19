from datetime import date
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


# One bought loan account that we are trying to recover money from.
class Account(Base):
    __tablename__ = "account"

    id: Mapped[int] = mapped_column(primary_key=True)
    loan_no: Mapped[str] = mapped_column(unique=True)
    portfolio: Mapped[str]
    seller_bank: Mapped[str]
    customer_name: Mapped[str]
    mobile: Mapped[str] = mapped_column(index=True)
    email: Mapped[str | None]
    city: Mapped[str | None]
    state: Mapped[str | None]
    office_id: Mapped[int] = mapped_column(ForeignKey("office.id"), index=True)
    language: Mapped[str | None]
    product: Mapped[str | None]
    original_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    outstanding: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    npa_date: Mapped[date | None]
    last_payment_date: Mapped[date | None]
    status: Mapped[str] = mapped_column(default="New", index=True)
    manager_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    owner_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True)
    total_paid: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=0, server_default="0"
    )
    next_followup: Mapped[date | None] = mapped_column(index=True)
