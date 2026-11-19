from datetime import date
from decimal import Decimal

from sqlalchemy import exists, func, select, update
from sqlalchemy.orm import Session

from app.models import Account, Ptp


# Adds a new Pending promise to pay (the caller commits afterwards).
def create_ptp(db: Session, account_id: int, user_id: str, amount: Decimal, promise_date: date) -> None:
    db.add(Ptp(account_id=account_id, user_id=user_id, amount=amount, promise_date=promise_date))
    db.flush()


# Returns the promise date of the account's earliest Pending promise, or None.
def earliest_pending_date(db: Session, account_id: int) -> date | None:
    return db.scalar(
        select(func.min(Ptp.promise_date)).where(Ptp.account_id == account_id, Ptp.state == "Pending")
    )


# Marks Pending promises dated today or later as Kept (used when a payment comes in); overdue ones are left alone.
def mark_ptps_kept(db: Session, account_id: int) -> None:
    db.execute(
        update(Ptp)
        .where(Ptp.account_id == account_id, Ptp.state == "Pending", Ptp.promise_date >= date.today())
        .values(state="Kept")
    )


# Pending promises dated before today become Broken; PTP accounts with no Pending promise go back to Working.
def mark_broken_ptps(db: Session) -> None:
    db.execute(
        update(Ptp).where(Ptp.state == "Pending", Ptp.promise_date < date.today()).values(state="Broken")
    )
    still_pending = exists().where(Ptp.account_id == Account.id, Ptp.state == "Pending")
    db.execute(update(Account).where(Account.status == "PTP", ~still_pending).values(status="Working"))
    db.commit()
