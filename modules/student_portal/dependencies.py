"""Зависимости FastAPI: текущий пользователь по токену, проверка роли, пагинация.

Пока в core/ нет общей зависимости get_current_user, модуль держит свою
(см. раздел 4.2 ТЗ). Токен выпускает core.auth.create_access_token,
проверяется тем же SECRET_KEY и алгоритмом HS256.
"""
from fastapi import Depends, HTTPException, Query, status
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from core.config import SECRET_KEY
from core.database import get_db
from core.models import User, UserRole

ALGORITHM = "HS256"

bearer_scheme = HTTPBearer(auto_error=False)


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Требуется авторизация",
        headers={"WWW-Authenticate": "Bearer"},
    )


def validation_error(location: tuple, message: str) -> RequestValidationError:
    """Ошибка 422 в стандартном формате FastAPI — для проверок вне Pydantic-схем."""
    return RequestValidationError([{"loc": location, "msg": message, "type": "value_error"}])


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise unauthorized()
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise unauthorized()
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise unauthorized()
    return user


def _role_checker(roles: tuple, detail: str):
    def check_role(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
        return user

    return check_role


get_current_student = _role_checker((UserRole.STUDENT,), "Доступ только для студентов")
get_current_admin = _role_checker((UserRole.ADMIN,), "Недостаточно прав")
get_current_teacher = _role_checker((UserRole.TEACHER,), "Недостаточно прав")


class Pagination:
    """Query-параметры page и page_size (по умолчанию 20, максимум 100)."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Номер страницы"),
        page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    ):
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    def wrap(self, items: list, total: int) -> dict:
        return {"items": items, "total": total, "page": self.page, "page_size": self.page_size}
