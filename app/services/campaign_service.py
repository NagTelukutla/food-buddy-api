from fastapi import HTTPException, status

from app.repositories.campaign_repository import CampaignRepository
from app.schemas.campaign import CampaignCreate, CampaignListResponse, CampaignResponse, CampaignUpdate


class CampaignService:
    def __init__(self, campaign_repo: CampaignRepository):
        self.campaign_repo = campaign_repo

    def list_campaigns(self, restaurant_id: int) -> CampaignListResponse:
        items = [CampaignResponse(**c) for c in self.campaign_repo.list_for_restaurant(restaurant_id)]
        return CampaignListResponse(items=items)

    def list_active(self, restaurant_id: int) -> CampaignListResponse:
        items = [CampaignResponse(**c) for c in self.campaign_repo.list_active(restaurant_id)]
        return CampaignListResponse(items=items)

    def create(self, payload: CampaignCreate, restaurant_id: int | None = None) -> CampaignResponse:
        data = payload.model_dump()
        if restaurant_id is not None:
            data["restaurant_id"] = restaurant_id
        created = self.campaign_repo.create(data)
        return CampaignResponse(**created)

    def update(
        self, campaign_id: int, payload: CampaignUpdate, restaurant_id: int | None = None
    ) -> CampaignResponse:
        campaign = self.campaign_repo.get_by_id(campaign_id)
        if not campaign:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
        if restaurant_id is not None and campaign.get("restaurant_id") != restaurant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Campaign does not belong to your restaurant",
            )
        updated = self.campaign_repo.update(campaign_id, payload.model_dump(exclude_unset=True))
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
        return CampaignResponse(**updated)
