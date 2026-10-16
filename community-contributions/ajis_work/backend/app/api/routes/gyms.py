from fastapi import APIRouter

from app.services.gym_service import find_nearby_gyms

router = APIRouter(
    prefix="/gyms",
    tags=["gyms"],
)


@router.get("/nearby")
async def nearby_gyms(
    latitude: float,
    longitude: float,
    radius: int = 3000,
):
    return await find_nearby_gyms(
        latitude=latitude,
        longitude=longitude,
        radius=radius,
    )