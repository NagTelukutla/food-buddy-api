from fastapi import APIRouter, Depends

from app.core.deps import get_review_service, get_tenant_context
from app.core.rbac import ROLE_ADMIN, ROLE_CUSTOMER, require_roles
from app.core.tenant import TenantContext, require_admin_tenant
from app.schemas.auth import TokenPayload
from app.schemas.review import ReviewCreate, ReviewListResponse, ReviewRespondRequest, ReviewResponse
from app.services.review_service import ReviewService

router = APIRouter(prefix="/api/reviews", tags=["Reviews"])


@router.post("", response_model=ReviewResponse)
def create_review(
    payload: ReviewCreate,
    current_user: TokenPayload = Depends(require_roles(ROLE_CUSTOMER)),
    service: ReviewService = Depends(get_review_service),
) -> ReviewResponse:
    return service.create(current_user.username, payload)


@router.get("/restaurant/{restaurant_id}", response_model=ReviewListResponse)
def list_restaurant_reviews(
    restaurant_id: int,
    service: ReviewService = Depends(get_review_service),
) -> ReviewListResponse:
    return service.list_for_restaurant(restaurant_id)


@router.put("/{review_id}/respond", response_model=ReviewResponse)
def respond_to_review(
    review_id: int,
    payload: ReviewRespondRequest,
    _: TokenPayload = Depends(require_roles(ROLE_ADMIN)),
    tenant: TenantContext = Depends(get_tenant_context),
    service: ReviewService = Depends(get_review_service),
) -> ReviewResponse:
    return service.respond(review_id, payload, restaurant_id=require_admin_tenant(tenant))
