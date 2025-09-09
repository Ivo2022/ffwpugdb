from starlette.templating import Jinja2Templates
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # Typically goes up one more level to project root

# Assumes your templates are in the "app/templates" folder
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
