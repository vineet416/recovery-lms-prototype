from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.templates import templates
from app.features.auth.service import check_login
from app.models import User

router = APIRouter()


# Home sends callers to their queue and everyone else to the account list (logged-out visitors go to /login).
@router.get("/")
def home(user: User = Depends(get_current_user)):
    return RedirectResponse("/accounts?view=queue" if user.role == "caller" else "/accounts", status_code=303)


# Shows the login form.
@router.get("/login")
def login_form(request: Request):
    return templates.TemplateResponse(request, "login.html", {"user": None})


# Checks the username and password, then starts the session or shows a friendly error.
@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(""),
    password: str = Form(""),
    db: Session = Depends(get_db),
):
    user = check_login(db, username, password)
    if user is None:
        context = {"user": None, "message": "Wrong username or password."}
        return templates.TemplateResponse(request, "login.html", context, status_code=401)
    request.session.clear()
    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=303)


# Ends the session and goes back to the login page.
@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
