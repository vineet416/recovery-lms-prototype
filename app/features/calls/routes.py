from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_role
from app.core.flash import set_flash
from app.features.calls.service import log_call
from app.models import User

router = APIRouter()


# Saves a call (with an optional promise) from the account page form, then returns to that page.
@router.post("/accounts/{account_id}/call")
def save_call(
    request: Request,
    account_id: int,
    disposition: str = Form(""),
    remarks: str = Form(""),
    next_followup: str = Form(""),
    promise_amount: str = Form(""),
    promise_date: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_role(user, ["caller"])
    try:
        log_call(db, user, account_id, disposition, remarks, next_followup, promise_amount, promise_date)
        set_flash(request, "Call saved.", "success")
    except ValueError as error:
        db.rollback()
        set_flash(request, str(error), "error")
    return RedirectResponse(f"/accounts/{account_id}", status_code=303)
