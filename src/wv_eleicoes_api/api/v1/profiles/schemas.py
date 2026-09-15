"""Public response contracts for the Profile 360 endpoint."""

from datetime import date

from pydantic import BaseModel


class PersonSummary(BaseModel):
    id: int
    legal_name: str
    display_name: str
    social_name: str | None
    birth_date: date | None
    birth_uf: str | None


class ExternalIdentifierSummary(BaseModel):
    source_system: str
    identifier_type: str
    identifier_value: str
    scope_key: str


class OfficeSummary(BaseModel):
    code: str | None
    name: str | None


class PartySummary(BaseModel):
    number: str | None
    acronym: str | None
    name: str | None


class CandidacySummary(BaseModel):
    election_year: int
    election_code: str
    election_round: int | None
    uf: str | None
    electoral_unit: str | None
    electoral_unit_name: str | None
    candidacy_sequence: str
    ballot_number: str | None
    ballot_name: str | None
    office: OfficeSummary
    party: PartySummary
    status_code: str | None
    status_name: str | None


class PersonProfileResponse(BaseModel):
    person: PersonSummary
    external_identifiers: list[ExternalIdentifierSummary]
    candidacies: list[CandidacySummary]
