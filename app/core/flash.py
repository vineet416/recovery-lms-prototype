from fastapi import Request


# Saves a one-time message in the session; kind is "success" or "error".
def set_flash(request: Request, text: str, kind: str = "success") -> None:
    request.session["flash"] = {"text": text, "kind": kind}


# Returns the saved message (or None) and removes it, so it is shown only once.
def pop_flash(request: Request) -> dict | None:
    return request.session.pop("flash", None)
