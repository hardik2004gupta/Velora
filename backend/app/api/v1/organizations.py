"""Organization management endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import Role
from app.database.session import get_db_session
from app.dependencies.auth import get_current_org, get_current_user, require_role
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.organization import (
    CreateOrganizationRequest,
    InviteMemberRequest,
    MemberResponse,
    OrganizationResponse,
    OrganizationWithRoleResponse,
    OrganizationsListResponse,
    UpdateMemberRoleRequest,
    UpdateOrganizationRequest,
)
from app.services.organization_service import OrganizationService

router = APIRouter()


@router.post("", status_code=201, response_model=OrganizationResponse, summary="Create organization")
async def create_org(
    payload: CreateOrganizationRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> OrganizationResponse:
    service = OrganizationService(db)
    org = await service.create(payload, owner=user, request_id=getattr(request.state, "request_id", ""))
    return OrganizationResponse(id=org.id, name=org.name, slug=org.slug, created_at=org.created_at)


@router.get("", response_model=OrganizationsListResponse, summary="List organizations for current user")
async def list_orgs(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> OrganizationsListResponse:
    service = OrganizationService(db)
    pairs = await service.list_for_user(user)
    items = [
        OrganizationWithRoleResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            created_at=org.created_at,
            role=membership.role,
        )
        for membership, org in pairs
    ]
    return OrganizationsListResponse(items=items, total=len(items))


@router.get("/{org_id}", response_model=OrganizationResponse, summary="Get organization")
async def get_org(
    org_and_membership: tuple[Organization, Membership] = Depends(get_current_org),
) -> OrganizationResponse:
    org, _ = org_and_membership
    return OrganizationResponse(id=org.id, name=org.name, slug=org.slug, created_at=org.created_at)


@router.patch("/{org_id}", response_model=OrganizationResponse, summary="Update organization")
async def update_org(
    org_id: uuid.UUID,
    payload: UpdateOrganizationRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> OrganizationResponse:
    service = OrganizationService(db)
    org = await service.update(org_id, payload, actor=user, request_id=getattr(request.state, "request_id", ""))
    return OrganizationResponse(id=org.id, name=org.name, slug=org.slug, created_at=org.created_at)


@router.delete("/{org_id}", status_code=204, summary="Delete organization")
async def delete_org(
    org_id: uuid.UUID,
    request: Request,
    _: tuple[Organization, Membership] = Depends(require_role(Role.OWNER)),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    service = OrganizationService(db)
    await service.delete(org_id, actor=user, request_id=getattr(request.state, "request_id", ""))


@router.get("/{org_id}/members", response_model=list[MemberResponse], summary="List organization members")
async def list_members(
    request: Request,
    user: User = Depends(get_current_user),
    org_and_membership: tuple[Organization, Membership] = Depends(get_current_org),
    db: AsyncSession = Depends(get_db_session),
) -> list[MemberResponse]:
    org, _ = org_and_membership
    service = OrganizationService(db)
    pairs = await service.list_members(org.id, actor=user)
    return [
        MemberResponse(
            user_id=member.id,
            email=member.email,
            full_name=member.full_name,
            role=membership.role,
            joined_at=membership.created_at,
        )
        for membership, member in pairs
    ]


@router.post("/{org_id}/members", status_code=201, response_model=MemberResponse, summary="Invite member")
async def invite_member(
    org_id: uuid.UUID,
    payload: InviteMemberRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> MemberResponse:
    user_repo = UserRepository(db)
    target_user = await user_repo.get_by_email(payload.email)
    if target_user is None:
        raise HTTPException(status_code=404, detail="User with that email not found.")
    service = OrganizationService(db)
    membership = await service.invite_member(
        org_id, payload, actor=user, target_user=target_user,
        request_id=getattr(request.state, "request_id", ""),
    )
    return MemberResponse(
        user_id=target_user.id,
        email=target_user.email,
        full_name=target_user.full_name,
        role=membership.role,
        joined_at=membership.created_at,
    )


@router.patch("/{org_id}/members/{target_user_id}", response_model=MemberResponse, summary="Update member role")
async def update_member_role(
    org_id: uuid.UUID,
    target_user_id: uuid.UUID,
    payload: UpdateMemberRoleRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> MemberResponse:
    user_repo = UserRepository(db)
    target_user = await user_repo.get_active_by_id(target_user_id)
    if target_user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    service = OrganizationService(db)
    membership = await service.update_member_role(
        org_id, target_user_id, payload, actor=user,
        request_id=getattr(request.state, "request_id", ""),
    )
    return MemberResponse(
        user_id=target_user.id,
        email=target_user.email,
        full_name=target_user.full_name,
        role=membership.role,
        joined_at=membership.created_at,
    )


@router.delete("/{org_id}/members/{target_user_id}", status_code=204, summary="Remove member")
async def remove_member(
    org_id: uuid.UUID,
    target_user_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    service = OrganizationService(db)
    await service.remove_member(org_id, target_user_id, actor=user, request_id=getattr(request.state, "request_id", ""))
