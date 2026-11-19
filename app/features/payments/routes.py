from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.flash import set_flash
from app.features.payments.service import record_payment
from app.models import User

router = APIRouter()


# Saves a payment from the account page form, then returns to that page.
@router.post("/accounts/{account_id}/payment")
def save_payment(
    request: Request,
    account_id: int,
    amount: str = Form(""),
    is_settlement: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_role(user, ["caller"])
    try:
        record_payment(db, user, account_id, amount, bool(is_settlement))
        set_flash(request, "Payment saved.", "success")
    except ValueError as error:
        db.rollback()
        set_flash(request, str(error), "error")
    return RedirectResponse(f"/accounts/{account_id}", status_code=303)
