from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import SECRET_KEY
from app.core.templates import templates
from app.features.auth.routes import router as auth_router

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.include_router(auth_router)


# Shows a friendly page for errors; a missing login (401) goes to the login page instead.
@app.exception_handler(HTTPException)
def friendly_http_error(request: Request, error: HTTPException):
    if error.status_code == 401:
        return RedirectResponse("/login", status_code=303)
    messages = {403: "You are not allowed to open this page.", 404: "Page not found."}
    message = messages.get(error.status_code, "Something went wrong. Please try again.")
    context = {"user": None, "message": message}
    return templates.TemplateResponse(request, "error.html", context, status_code=error.status_code)


# Catches any unexpected crash so the user never sees a traceback.
@app.exception_handler(Exception)
def friendly_crash(request: Request, error: Exception):
    context = {"user": None, "message": "Something went wrong. Please try again."}
    return templates.TemplateResponse(request, "error.html", context, status_code=500)
