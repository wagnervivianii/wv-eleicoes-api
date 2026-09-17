"""Person-centered public HTTP contracts for declared assets."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, status

from wv_eleicoes_api.api.v1.assets.repository import (
    fetch_asset_declaration_detail,
    fetch_asset_evolution,
    fetch_asset_history,
)
from wv_eleicoes_api.api.v1.assets.schemas import (
    AssetDeclarationDetailResponse,
    AssetEvolutionResponse,
    AssetHistoryResponse,
)

router = APIRouter(prefix="/people", tags=["assets"])

PersonId = Annotated[
    int,
    Path(gt=0, description="Stable core.person identifier"),
]
ElectionYear = Annotated[
    int,
    Path(ge=1900, le=9999, description="Election year"),
]
ElectionCode = Annotated[
    str,
    Path(
        min_length=1,
        max_length=32,
        pattern=r"^[0-9]+$",
        description="TSE election code",
    ),
]
CandidacySequence = Annotated[
    str,
    Path(
        min_length=1,
        max_length=64,
        pattern=r"^[0-9]+$",
        description="TSE candidacy sequence scoped by election",
    ),
]


@router.get("/{person_id}/assets", response_model=AssetHistoryResponse)
def get_asset_history(person_id: PersonId) -> AssetHistoryResponse:
    """Return declared-assets snapshots ordered from newest election to oldest."""

    history = fetch_asset_history(person_id)
    if history is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found",
        )
    return history


@router.get("/{person_id}/assets/evolution", response_model=AssetEvolutionResponse)
def get_asset_evolution(person_id: PersonId) -> AssetEvolutionResponse:
    """Return annual asset evolution exactly as published by ANALYTICS."""

    evolution = fetch_asset_evolution(person_id)
    if evolution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found",
        )
    return evolution


@router.get(
    "/{person_id}/assets/declarations/"
    "{election_year}/{election_code}/{candidacy_sequence}",
    response_model=AssetDeclarationDetailResponse,
)
def get_asset_declaration_detail(
    person_id: PersonId,
    election_year: ElectionYear,
    election_code: ElectionCode,
    candidacy_sequence: CandidacySequence,
) -> AssetDeclarationDetailResponse:
    """Return one declaration selected by its complete candidacy-scoped key."""

    person_exists, declaration = fetch_asset_declaration_detail(
        person_id,
        election_year,
        election_code,
        candidacy_sequence,
    )
    if not person_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found",
        )
    if declaration is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset declaration not found",
        )
    return declaration
