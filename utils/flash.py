# utils/flash.py (or in your main app file)
from starlette.requests import Request

def flash(request: Request, message: str, category: str = "info"):
    """
    Store a flash message in session.
    - category: 'info', 'success', 'error', etc.
    """
    if "_flashes" not in request.session:
        request.session["_flashes"] = []
    request.session["_flashes"].append({"message": message, "category": category})

def get_flashed_messages(request: Request):
    """
    Pop all flash messages from session and return them.
    """
    messages = request.session.pop("_flashes", [])
    return messages
