from fastapi.templating import Jinja2Templates

from app.core.flash import pop_flash

# One shared template renderer, so every routes file uses the same templates folder.
templates = Jinja2Templates(directory="app/templates")
# Lets _flash.html read and clear the one-time message without every route passing it.
templates.env.globals["pop_flash"] = pop_flash
