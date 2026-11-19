from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from app.core.constants import DISPOSITIONS, FINAL_STATUSES
from app.features.accounts.visibility import accounts_visible_to
from app.features.promises.service import create_ptp, earliest_pending_date
from app.models import Account, CallLog, User


# Turns a date typed in the form into a date; blank gives None, bad or past dates raise ValueError.
def read_future_date(text: str, label: str) -> date | None:
    if not text.strip():
        return None
    try:
        value = date.fromisoformat(text.strip())
    except ValueError:
        raise ValueError(f"{label} is not a valid date.")
    if value < date.today():
        raise ValueError(f"{label} cannot be in the past.")
    return value


# Reads the promise amount; it must be a number above zero.
def read_promise_amount(text: str) -> Decimal:
    try:
        amount = Decimal(text.strip())
    except InvalidOperation:
        raise ValueError("Promise amount must be a number.")
    if not amount.is_finite() or amount <= 0:
        raise ValueError("Promise amount must be more than zero.")
    return amount


# Saves one call (and its promise, if any) on one of the caller's own open accounts.
def log_call(
    db: Session, user: User, account_id: int, disposition: str, remarks: str,
    followup_text: str, amount_text: str, promise_date_text: str,
) -> None:
    account = db.scalars(accounts_visible_to(user).where(Account.id == account_id)).first()
    if account is None:
        raise ValueError("Account not found.")
    if account.status in FINAL_STATUSES:
        raise ValueError("This account is closed. No more calls can be logged.")
    if disposition not in DISPOSITIONS:
        raise ValueError("Please choose a disposition.")
    followup = read_future_date(followup_text, "Follow-up date")
    promise = disposition == "Promise to pay"
    if promise:
        amount = read_promise_amount(amount_text)
        promise_date = read_future_date(promise_date_text, "Promise date")
        if promise_date is None:
            raise ValueError("Promise date is required.")
        create_ptp(db, account.id, user.id, amount, promise_date)
    db.add(CallLog(account_id=account.id, user_id=user.id, disposition=disposition,
                   remarks=remarks.strip() or None, next_followup=followup))
    if promise:
        account.status = "PTP"
    elif account.status == "New":
        account.status = "Working"
    account.next_followup = followup or earliest_pending_date(db, account.id)
    db.commit()
