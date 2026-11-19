from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from app.core.constants import FINAL_STATUSES
from app.features.accounts.visibility import accounts_visible_to
from app.features.promises.service import earliest_pending_date, mark_ptps_kept
from app.models import Account, Payment, User


# Reads the payment amount; it must be a number above zero.
def read_payment_amount(text: str) -> Decimal:
    try:
        amount = Decimal(text.strip())
    except InvalidOperation:
        raise ValueError("Payment amount must be a number.")
    if not amount.is_finite() or amount <= 0:
        raise ValueError("Payment amount must be more than zero.")
    return amount


# Saves one payment on one of the caller's own open accounts and updates status and promises.
def record_payment(db: Session, user: User, account_id: int, amount_text: str, is_settlement: bool) -> None:
    query = accounts_visible_to(user).where(Account.id == account_id).with_for_update()
    account = db.scalars(query).first()
    if account is None:
        raise ValueError("Account not found.")
    if account.status in FINAL_STATUSES:
        raise ValueError("This account is closed. No more payments can be recorded.")
    amount = read_payment_amount(amount_text)
    db.add(Payment(account_id=account.id, user_id=user.id, amount=amount,
                   paid_on=date.today(), is_settlement=is_settlement))
    account.total_paid += amount  # outstanding is never changed by a payment
    if is_settlement:
        account.status = "Settled"
    elif account.total_paid >= account.outstanding:
        account.status = "Closed"
    else:
        account.status = "Part-paid"
    mark_ptps_kept(db, account.id)
    if account.status in FINAL_STATUSES:
        account.next_followup = None
    else:
        account.next_followup = earliest_pending_date(db, account.id)
    db.commit()
