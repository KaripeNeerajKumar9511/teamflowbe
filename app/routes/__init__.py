from app.routes.auth import auth_bp
from app.routes.projects import projects_bp
from app.routes.tasks import tasks_bp
from app.routes.users import users_bp

__all__ = ["auth_bp", "projects_bp", "tasks_bp", "users_bp"]
