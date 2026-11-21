
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.calculation import Calculation
from app.schemas.calculation import (
    CalculationCreate,
    CalculationRead,
)
from app.operations.factory import CalculationFactory

router = APIRouter(
    prefix="/calculations",
    tags=["Calculations"],
)


@router.post(
    "",
    response_model=CalculationRead,
    status_code=status.HTTP_201_CREATED,
)
def add_calculation(
    payload: CalculationCreate,
    db: Session = Depends(get_db),
):
    """Calculate a result and save it in PostgreSQL."""

    try:
        result = CalculationFactory.calculate(
            payload.a,
            payload.b,
            payload.type,
        )

        calculation = Calculation(
            a=payload.a,
            b=payload.b,
            type=payload.type.value,
            result=result,
        )

        db.add(calculation)
        db.commit()
        db.refresh(calculation)

        return calculation

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[CalculationRead],
    status_code=status.HTTP_200_OK,
)
def browse_calculations(
    db: Session = Depends(get_db),
):
    """Retrieve all saved calculations."""

    calculations = (
        db.query(Calculation)
        .order_by(Calculation.id.asc())
        .all()
    )

    return calculations
