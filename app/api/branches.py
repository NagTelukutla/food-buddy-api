from fastapi import APIRouter, Depends

from app.core.deps import get_branch_repository, get_tenant_context
from app.core.rbac import ROLE_ADMIN, require_roles
from app.core.tenant import TenantContext, assert_restaurant_access
from app.repositories.branch_repository import BranchRepository
from app.schemas.auth import TokenPayload
from app.schemas.branch import BranchResponse, BranchUpdate
from fastapi import HTTPException, status

router = APIRouter(prefix="/api/branches", tags=["Branches"])


@router.get("/{branch_id}", response_model=BranchResponse)
def get_branch(
    branch_id: int,
    branch_repo: BranchRepository = Depends(get_branch_repository),
) -> BranchResponse:
    branch = branch_repo.get_by_id(branch_id)
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    return BranchResponse(**branch)


@router.put("/{branch_id}", response_model=BranchResponse)
def update_branch(
    branch_id: int,
    payload: BranchUpdate,
    _: TokenPayload = Depends(require_roles(ROLE_ADMIN)),
    tenant: TenantContext = Depends(get_tenant_context),
    branch_repo: BranchRepository = Depends(get_branch_repository),
) -> BranchResponse:
    branch = branch_repo.get_by_id(branch_id)
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    assert_restaurant_access(tenant, branch["restaurant_id"])
    updated = branch_repo.update(branch_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    return BranchResponse(**updated)


@router.delete("/{branch_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_branch(
    branch_id: int,
    _: TokenPayload = Depends(require_roles(ROLE_ADMIN)),
    tenant: TenantContext = Depends(get_tenant_context),
    branch_repo: BranchRepository = Depends(get_branch_repository),
) -> None:
    branch = branch_repo.get_by_id(branch_id)
    if not branch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    assert_restaurant_access(tenant, branch["restaurant_id"])
    if not branch_repo.deactivate(branch_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
