"""Shared helpers for dashboard focal-point contact lists."""

from __future__ import annotations

from sqlalchemy import or_

from app import db
from app.models import User
from app.models.core import UserEntityPermission
from app.models.rbac import RbacRole, RbacUserRole


def _serialize_focal_point(user: User) -> dict:
    return {
        'id': user.id,
        'name': (user.name or '').strip() or None,
        'title': (user.title or '').strip() or None,
        'email': user.email,
    }


def get_focal_points_for_country(country_id: int) -> tuple[list[dict], list[dict]]:
    """
    Return (national_society_focal_points, organization_focal_points) for a country.

    Mirrors main.dashboard categorization: assignment_editor_submitter users with
    country permission, split by org email domain and excluding admin/system_manager roles.
    """
    return _focal_points_for_entity('country', country_id)


def get_focal_points_for_initiative(initiative_id: int) -> tuple[list[dict], list[dict]]:
    """Same split for a funded initiative: the users granted access to that initiative itself."""
    return _focal_points_for_entity('initiative', initiative_id)


def get_focal_point_users_for_initiative(initiative_id: int) -> tuple[list[User], list[User]]:
    """Like get_focal_points_for_initiative, but as User objects (the dashboard template needs them)."""
    return _split_focal_point_users('initiative', initiative_id)


def _focal_points_for_entity(entity_type: str, entity_id: int) -> tuple[list[dict], list[dict]]:
    ns_users, org_users = _split_focal_point_users(entity_type, entity_id)
    return [_serialize_focal_point(fp) for fp in ns_users], [_serialize_focal_point(fp) for fp in org_users]


def _split_focal_point_users(entity_type: str, entity_id: int) -> tuple[list[User], list[User]]:
    from app.utils.organization_helpers import is_org_email

    all_focal_points = (
        User.query
        .join(UserEntityPermission, User.id == UserEntityPermission.user_id)
        .join(RbacUserRole, User.id == RbacUserRole.user_id)
        .join(RbacRole, RbacUserRole.role_id == RbacRole.id)
        .filter(
            RbacRole.code == 'assignment_editor_submitter',
            UserEntityPermission.entity_type == entity_type,
            UserEntityPermission.entity_id == entity_id,
        )
        .distinct()
        .order_by(User.name)
        .all()
    )

    admin_role_user_ids = set(
        uid for (uid,) in db.session.query(RbacUserRole.user_id)
        .join(RbacRole, RbacUserRole.role_id == RbacRole.id)
        .filter(or_(
            RbacRole.code == 'system_manager',
            RbacRole.code.like('admin_%'),
        ))
        .all()
    )

    ns_focal_points = [fp for fp in all_focal_points if not is_org_email(fp.email)]
    org_focal_points = [
        fp for fp in all_focal_points
        if is_org_email(fp.email) and fp.id not in admin_role_user_ids
    ]
    return ns_focal_points, org_focal_points
