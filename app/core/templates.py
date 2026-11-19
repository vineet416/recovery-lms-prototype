from fastapi.templating import Jinja2Templates

# One shared template renderer, so every routes file uses the same templates folder.
templates = Jinja2Templates(directory="app/templates")
