"""Person-centered public HTTP contracts."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, status

from wv_eleicoes_api.api.v1.profiles.repository import (
    fetch_electoral_history,
    fetch_person_profile,
)
from wv_eleicoes_api.api.v1.profiles.schemas import (
    ElectoralHistoryResponse,
    PersonProfileResponse,
)

router = APIRouter(prefix="/people", tags=["profiles"])

PersonId = Annotated[
    int,
    Path(gt=0, description="Stable core.person identifier"),
]


@router.get("/{person_id}/profile", response_model=PersonProfileResponse)
def get_person_profile(person_id: PersonId) -> PersonProfileResponse:
    """Return the public Profile 360 for one stable political person."""

    profile = fetch_person_profile(person_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found",
        )
    return profile


@router.get("/{person_id}/electoral-history", response_model=ElectoralHistoryResponse)
def get_electoral_history(person_id: PersonId) -> ElectoralHistoryResponse:
    """Return published candidacies ordered from newest election to oldest."""

    history = fetch_electoral_history(person_id)
    if history is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found",
        )
    return history
