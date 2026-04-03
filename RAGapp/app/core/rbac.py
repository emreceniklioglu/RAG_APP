"""
Simple role-based access control.
Maps user roles to the departments they are allowed to query.
"""

from app.core.logging import logger

# Role -> allowed departments mapping
ROLE_PERMISSIONS: dict[str, list[str]] = {
    "technician": ["maintenance"],
    "engineer": ["engineering", "maintenance"],
    "hr_staff": ["hr"],
}


def get_allowed_departments(user_role: str) -> list[str]:
    """Return list of departments accessible to the given role.

    Raises ValueError if the role is not recognized.
    """
    role = user_role.strip().lower()
    if role not in ROLE_PERMISSIONS:
        valid_roles = ", ".join(sorted(ROLE_PERMISSIONS.keys()))
        logger.warning("Invalid role attempted: %s", user_role)
        raise ValueError(
            f"Geçersiz kullanıcı rolü: '{user_role}'. "
            f"Geçerli roller: {valid_roles}"
        )
    return ROLE_PERMISSIONS[role]


def is_valid_role(user_role: str) -> bool:
    """Check if a role exists in the RBAC config."""
    return user_role.strip().lower() in ROLE_PERMISSIONS
