from fastapi import HTTPException, status

from app.repositories.customer_repository import CustomerRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.user_repository import UserRepository
from app.schemas.review import ReviewCreate, ReviewListResponse, ReviewRespondRequest, ReviewResponse


class ReviewService:
    def __init__(
        self,
        review_repo: ReviewRepository,
        order_repo: OrderRepository,
        user_repo: UserRepository,
        customer_repo: CustomerRepository,
    ):
        self.review_repo = review_repo
        self.order_repo = order_repo
        self.user_repo = user_repo
        self.customer_repo = customer_repo

    def create(self, username: str, payload: ReviewCreate) -> ReviewResponse:
        order = self.order_repo.get_by_order_id(payload.order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        if order.status != "Delivered":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reviews are allowed only for delivered orders",
            )
        if self.review_repo.get_by_order_id(payload.order_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Review already exists")
        user = self.user_repo.get_by_username(username)
        customer_id = None
        if user:
            customer = self.customer_repo.get_by_user_id(user["id"])
            if customer:
                customer_id = customer["id"]
        created = self.review_repo.create(
            {
                "order_id": payload.order_id,
                "restaurant_id": payload.restaurant_id,
                "customer_id": customer_id,
                "rating": payload.rating,
                "comment": payload.comment,
            }
        )
        return ReviewResponse(**created)

    def list_for_restaurant(self, restaurant_id: int) -> ReviewListResponse:
        items = [ReviewResponse(**r) for r in self.review_repo.list_for_restaurant(restaurant_id)]
        return ReviewListResponse(items=items)

    def respond(
        self, review_id: int, payload: ReviewRespondRequest, restaurant_id: int | None = None
    ) -> ReviewResponse:
        review = self.review_repo.get_by_id(review_id)
        if not review:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
        if restaurant_id is not None and review.get("restaurant_id") != restaurant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Review does not belong to your restaurant",
            )
        updated = self.review_repo.add_response(review_id, payload.owner_response)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
        return ReviewResponse(**updated)
