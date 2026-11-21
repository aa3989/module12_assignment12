
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

"""Create operation for calculations is implemented below. This endpoint allows users to perform a calculation based on the provided input and save the result in the PostgreSQL database. The add_calculation function takes a CalculationCreate payload, computes the result using the CalculationFactory, and stores the calculation in the database. If any errors occur during the process, appropriate HTTP exceptions are raised."""
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

"""Read operations for calculations are implemented below. These endpoints allow users to retrieve all saved calculations or a specific calculation by its ID. The browse_calculations endpoint returns a list of all calculations, while the read_calculation endpoint retrieves a single calculation based on the provided ID, returning a 404 error if the calculation does not exist."""
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


@router.get(
    "/{calculation_id}",
    response_model=CalculationRead,
    status_code=status.HTTP_200_OK,
)
def read_calculation(
    calculation_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve a calculation by its ID."""

    calculation = db.get(Calculation, calculation_id)

    if calculation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calculation not found",
        )

    return calculation


"""Edit and delete operations for calculations are implemented below. These endpoints allow users to update an existing calculation and recompute the result, as well as delete a calculation by its ID. The update operation checks if the calculation exists, recalculates the result based on the new input, and updates the database accordingly. The delete operation checks for existence and removes the calculation from the database if found."""
@router.put(
    "/{calculation_id}",
    response_model=CalculationRead,
    status_code=status.HTTP_200_OK,
)
def update_calculation(
    calculation_id: int,
    payload: CalculationCreate,
    db: Session = Depends(get_db),
):
    """Update an existing calculation and recompute result."""

    calculation = db.get(Calculation, calculation_id)

    if calculation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calculation not found",
        )

    try:
        new_result = CalculationFactory.calculate(
            payload.a,
            payload.b,
            payload.type,
        )

        calculation.a = payload.a
        calculation.b = payload.b
        calculation.type = payload.type.value
        calculation.result = new_result

        db.commit()
        db.refresh(calculation)

        return calculation

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc



"""Delete operation for calculations is implemented below. This endpoint allows users to delete a calculation by its ID. The delete_calculation function checks if the calculation exists in the database and removes it if found, returning a 204 No Content status code. If the calculation does not exist, a 404 Not Found error is raised."""
@router.delete(
    "/{calculation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_calculation(
    calculation_id: int,
    db: Session = Depends(get_db),
):
    """Delete a calculation by its ID."""

    calculation = db.get(Calculation, calculation_id)

    if calculation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calculation not found",
        )

    db.delete(calculation)
    db.commit()

