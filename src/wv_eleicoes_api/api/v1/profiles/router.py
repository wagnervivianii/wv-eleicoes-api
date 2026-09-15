"""Profile 360 HTTP contract."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, status

from wv_eleicoes_api.api.v1.profiles.repository import fetch_person_profile
from wv_eleicoes_api.api.v1.profiles.schemas import PersonProfileResponse

router = APIRouter(prefix="/people", tags=["profiles"])


@router.get("/{person_id}/profile", response_model=PersonProfileResponse)
def get_person_profile(
    person_id: Annotated[
        int,
        Path(gt=0, description="Stable core.person identifier"),
    ],
) -> PersonProfileResponse:
    """Return the public Profile 360 for one stable political person."""

    profile = fetch_person_profile(person_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found",
        )
    return profile
