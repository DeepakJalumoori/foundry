from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.schemas.m4 import (
    CompanyDetailResponse,
    CompanyFoundersResponse,
    CompanyFundingResponse,
    CompanyHiringSignalsResponse,
    CompanyListResponse,
    CompanyStage,
    OpportunityType,
)
from app.schemas.run import ErrorResponse
from app.services.discovery_orchestrator import (
    get_company_detail,
    get_company_founders,
    get_company_funding,
    get_company_hiring_signals,
    list_companies,
    refresh_company_intelligence,
)

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=CompanyListResponse)
def list_discovered_companies(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    stage: CompanyStage | None = None,
    opportunity_type: OpportunityType | None = None,
    industry: str | None = None,
    db: Session = Depends(get_db),
) -> CompanyListResponse:
    """List discovered startup companies with pagination and optional filters."""
    return list_companies(
        db,
        limit=limit,
        offset=offset,
        stage=stage,
        opportunity_type=opportunity_type,
        industry=industry,
    )


@router.get(
    "/{company_id}",
    response_model=CompanyDetailResponse,
    responses={404: {"model": ErrorResponse}},
)
def retrieve_company(
    company_id: str,
    db: Session = Depends(get_db),
) -> CompanyDetailResponse:
    """Retrieve normalized company profile, latest research, and evidence."""
    return get_company_detail(db, company_id)


@router.post(
    "/{company_id}/research",
    response_model=CompanyDetailResponse,
    responses={404: {"model": ErrorResponse}, 503: {"model": ErrorResponse}},
)
def trigger_company_research(
    company_id: str,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> CompanyDetailResponse:
    """Trigger or refresh company research, funding, hiring signals, and founders."""
    return refresh_company_intelligence(db, settings, company_id)


@router.get(
    "/{company_id}/funding",
    response_model=CompanyFundingResponse,
    responses={404: {"model": ErrorResponse}},
)
def retrieve_company_funding(
    company_id: str,
    db: Session = Depends(get_db),
) -> CompanyFundingResponse:
    """Retrieve funding events and source evidence for a company."""
    return get_company_funding(db, company_id)


@router.get(
    "/{company_id}/hiring-signals",
    response_model=CompanyHiringSignalsResponse,
    responses={404: {"model": ErrorResponse}},
)
def retrieve_company_hiring_signals(
    company_id: str,
    db: Session = Depends(get_db),
) -> CompanyHiringSignalsResponse:
    """Retrieve classified hiring signals and job opportunities for a company."""
    return get_company_hiring_signals(db, company_id)


@router.get(
    "/{company_id}/founders",
    response_model=CompanyFoundersResponse,
    responses={404: {"model": ErrorResponse}},
)
def retrieve_company_founders(
    company_id: str,
    db: Session = Depends(get_db),
) -> CompanyFoundersResponse:
    """Retrieve discovered founders and source evidence for a company."""
    return get_company_founders(db, company_id)
