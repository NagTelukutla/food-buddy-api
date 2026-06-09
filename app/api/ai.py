from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/api/ai", tags=["AI (Deferred)"])


@router.post("/recommend")
def ai_recommend():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="AI features are not yet available",
    )


@router.post("/chat")
def ai_chat():
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="AI features are not yet available",
    )
