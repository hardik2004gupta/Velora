"""Organization service — tenant management and member RBAC."""

from __future__ import annotations

import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.core.rbac import Permission, Role, has_permission, role_satisfies
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.user import User
from app.repositories.membership_repository import MembershipRepository
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.organization import (
    CreateOrganizationRequest,
    InviteMemberRequest,
    UpdateMemberRoleRequest,
    UpdateOrganizationRequest,
)

log = get_logger(__name__)


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    return slug[:48].strip("-")


class OrganizationService:
    def __init__(
        self,
        db: AsyncSession,
        org_repo: OrganizationRepository | None = None,
        membership_repo: MembershipRepository | None = None,
    ) -> None:
        self._db = db
        self._org_repo = org_repo or OrganizationRepository(db)
        self._membership_repo = membership_repo or MembershipRepository(db)

    async def create(
        self,
        payload: CreateOrganizationRequest,
        *,
        owner: User,
        request_id: str = "",
    ) -> Organization:
        base_slug = _slugify(payload.name)
        slug = base_slug
        suffix = 1
        while await self._org_repo.slug_exists(slug):
            slug = f"{base_slug}-{suffix}"
            suffix += 1

        org = await self._org_repo.create(name=payload.name, slug=slug)
        await self._membership_repo.create(
            user_id=owner.id, org_id=org.id, role=Role.OWNER
        )
        log.info(
            "org_created",
            org_id=str(org.id),
            owner_id=str(owner.id),
            request_id=request_id,
        )
        return org

    async def list_for_user(self, user: User) -> list[tuple[Membership, Organization]]:
        return await self._membership_repo.get_orgs_for_user(user.id)

    async def get(self, org_id: uuid.UUID, *, actor: User) -> Organization:
        org = await self._org_repo.get(org_id)
        if org is None:
            raise NotFoundError("Organization not found.")
        membership = await self._membership_repo.get_by_user_and_org(actor.id, org_id)
        if membership is None:
            raise NotFoundError("Organization not found.")
        return org

    async def update(
        self,
        org_id: uuid.UUID,
        payload: UpdateOrganizationRequest,
        *,
        actor: User,
        request_id: str = "",
    ) -> Organization:
        org = await self._get_org_with_permission(org_id, actor, Permission.UPDATE_ORGANIZATION)
        if payload.name is not None:
            org = await self._org_repo.update_name(org, payload.name)
        log.info("org_updated", org_id=str(org_id), request_id=request_id)
        return org

    async def delete(
        self,
        org_id: uuid.UUID,
        *,
        actor: User,
        request_id: str = "",
    ) -> None:
        org = await self._get_org_with_permission(org_id, actor, Permission.DELETE_ORGANIZATION)
        # Cascade deletes handle memberships and api_keys
        await self._org_repo.delete(org)
        log.info("org_deleted", org_id=str(org_id), request_id=request_id)

    async def list_members(
        self, org_id: uuid.UUID, *, actor: User
    ) -> list[tuple[Membership, User]]:
        await self._get_org_with_permission(org_id, actor, Permission.VIEW_MEMBERS)
        return await self._membership_repo.get_members_of_org(org_id)

    async def invite_member(
        self,
        org_id: uuid.UUID,
        payload: InviteMemberRequest,
        *,
        actor: User,
        target_user: User,
        request_id: str = "",
    ) -> Membership:
        await self._get_org_with_permission(org_id, actor, Permission.MANAGE_MEMBERS)
        existing = await self._membership_repo.get_by_user_and_org(target_user.id, org_id)
        if existing is not None:
            raise ConflictError("User is already a member of this organization.")
        membership = await self._membership_repo.create(
            user_id=target_user.id, org_id=org_id, role=payload.role
        )
        log.info(
            "member_invited",
            org_id=str(org_id),
            target_id=str(target_user.id),
            role=payload.role,
            request_id=request_id,
        )
        return membership

    async def update_member_role(
        self,
        org_id: uuid.UUID,
        target_user_id: uuid.UUID,
        payload: UpdateMemberRoleRequest,
        *,
        actor: User,
        request_id: str = "",
    ) -> Membership:
        await self._get_org_with_permission(org_id, actor, Permission.MANAGE_MEMBERS)
        membership = await self._membership_repo.get_by_user_and_org(target_user_id, org_id)
        if membership is None:
            raise NotFoundError("Member not found in this organization.")
        if payload.role == Role.OWNER:
            raise ForbiddenError("Cannot assign owner role via this endpoint. Use transfer ownership.")
        updated = await self._membership_repo.update_role(membership, payload.role)
        log.info(
            "member_role_updated",
            org_id=str(org_id),
            target_id=str(target_user_id),
            new_role=payload.role,
            request_id=request_id,
        )
        return updated

    async def remove_member(
        self,
        org_id: uuid.UUID,
        target_user_id: uuid.UUID,
        *,
        actor: User,
        request_id: str = "",
    ) -> None:
        await self._get_org_with_permission(org_id, actor, Permission.MANAGE_MEMBERS)
        membership = await self._membership_repo.get_by_user_and_org(target_user_id, org_id)
        if membership is None:
            raise NotFoundError("Member not found in this organization.")
        if membership.role == Role.OWNER:
            owner_count = await self._membership_repo.count_owners(org_id)
            if owner_count <= 1:
                raise ForbiddenError("Cannot remove the last owner of an organization.")
        await self._membership_repo.delete(membership)
        log.info(
            "member_removed",
            org_id=str(org_id),
            target_id=str(target_user_id),
            request_id=request_id,
        )

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    async def _get_org_with_permission(
        self, org_id: uuid.UUID, actor: User, permission: Permission
    ) -> Organization:
        org = await self._org_repo.get(org_id)
        if org is None:
            raise NotFoundError("Organization not found.")
        membership = await self._membership_repo.get_by_user_and_org(actor.id, org_id)
        if membership is None:
            raise NotFoundError("Organization not found.")
        if not has_permission(membership.role, permission):
            raise ForbiddenError(
                f"Role '{membership.role}' does not have permission '{permission}'."
            )
        return org
