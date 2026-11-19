from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import SECRET_KEY
from app.core.templates import templates
from app.features.accounts.routes import router as accounts_router
from app.features.allocation.routes import router as allocation_router
from app.features.auth.routes import router as auth_router
from app.features.calls.routes import router as calls_router
from app.features.upload.routes import router as upload_router

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(accounts_router)
app.include_router(allocation_router)
app.include_router(calls_router)


# Shows a friendly page for errors; a missing login (401) goes to the login page instead.
@app.exception_handler(HTTPException)
def friendly_http_error(request: Request, error: HTTPException):
    if error.status_code == 401:
        return RedirectResponse("/login", status_code=303)
    messages = {403: "You are not allowed to open this page.", 404: "Page not found."}
    message = messages.get(error.status_code, "Something went wrong. Please try again.")
    context = {"user": None, "message": message}
    return templates.TemplateResponse(request, "error.html", context, status_code=error.status_code)


# A badly typed address like /accounts/abc shows the same friendly "Page not found" page.
@app.exception_handler(RequestValidationError)
def friendly_bad_input(request: Request, error: RequestValidationError):
    return friendly_http_error(request, HTTPException(status_code=404))


# Catches any unexpected crash so the user never sees a traceback.
@app.exception_handler(Exception)
def friendly_crash(request: Request, error: Exception):
    context = {"user": None, "message": "Something went wrong. Please try again."}
    return templates.TemplateResponse(request, "error.html", context, status_code=500)
