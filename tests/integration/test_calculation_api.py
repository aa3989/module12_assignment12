"""Integration tests for Calculation BREAD API endpoints."""

import pytest

from app.models.calculation import Calculation
from app.operations.factory import CalculationFactory

def sample_calculation():
    """Return a valid calculation request."""
    return {
        "a": 10.0,
        "b": 5.0,
        "type": "Add",
    }


# ============================================================
# ADD - POST /calculations
# ============================================================

def test_create_calculation(client, db_session):
    """Create a calculation and verify database persistence."""

    response = client.post(
        "/calculations",
        json=sample_calculation(),
    )

    assert response.status_code == 201

    data = response.json()

    assert "id" in data
    assert data["a"] == 10.0
    assert data["b"] == 5.0
    assert data["type"] == "Add"
    assert data["result"] == 15.0

    stored = db_session.get(Calculation, data["id"])

    assert stored is not None
    assert stored.result == 15.0
    assert stored.type == "Add"


# ============================================================
# BROWSE - GET /calculations
# ============================================================

def test_browse_calculations(client):
    """Retrieve all saved calculations."""

    first = client.post(
        "/calculations",
        json={"a": 10.0, "b": 5.0, "type": "Add"},
    )

    second = client.post(
        "/calculations",
        json={"a": 20.0, "b": 4.0, "type": "Divide"},
    )

    assert first.status_code == 201
    assert second.status_code == 201

    response = client.get("/calculations")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 2

    ids = {item["id"] for item in data}

    assert first.json()["id"] in ids
    assert second.json()["id"] in ids


# ============================================================
# READ - GET /calculations/{id}
# ============================================================

def test_read_calculation(client):
    """Retrieve one calculation by its ID."""

    created = client.post(
        "/calculations",
        json=sample_calculation(),
    )

    assert created.status_code == 201
    calculation_id = created.json()["id"]

    response = client.get(
        f"/calculations/{calculation_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == calculation_id
    assert data["a"] == 10.0
    assert data["b"] == 5.0
    assert data["type"] == "Add"
    assert data["result"] == 15.0


# ============================================================
# EDIT - PUT /calculations/{id}
# ============================================================

def test_update_calculation(client, db_session):
    """Update calculation inputs and recompute the result."""

    created = client.post(
        "/calculations",
        json=sample_calculation(),
    )

    assert created.status_code == 201
    calculation_id = created.json()["id"]

    response = client.put(
        f"/calculations/{calculation_id}",
        json={
            "a": 20.0,
            "b": 4.0,
            "type": "Divide",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == calculation_id
    assert data["a"] == 20.0
    assert data["b"] == 4.0
    assert data["type"] == "Divide"
    assert data["result"] == 5.0

    # Verify the database contains the updated record.
    db_session.expire_all()
    stored = db_session.get(Calculation, calculation_id)

    assert stored is not None
    assert stored.type == "Divide"
    assert stored.result == 5.0


# ============================================================
# DELETE - DELETE /calculations/{id}
# ============================================================

def test_delete_calculation(client, db_session):
    """Delete a calculation from the database."""

    created = client.post(
        "/calculations",
        json=sample_calculation(),
    )

    assert created.status_code == 201
    calculation_id = created.json()["id"]

    response = client.delete(
        f"/calculations/{calculation_id}"
    )

    assert response.status_code == 204
    assert response.content == b""

    # Confirm the record no longer exists.
    db_session.expire_all()

    stored = db_session.get(Calculation, calculation_id)

    assert stored is None

    # Reading the deleted record should return 404.
    missing = client.get(
        f"/calculations/{calculation_id}"
    )

    assert missing.status_code == 404


# ============================================================
# TEST ALL ARITHMETIC OPERATIONS
# ============================================================

@pytest.mark.parametrize(
    "operation,expected",
    [
        ("Add", 15.0),
        ("Sub", 5.0),
        ("Multiply", 50.0),
        ("Divide", 2.0),
    ],
)
def test_arithmetic_operations(client, operation, expected):
    """Verify all supported calculation operations."""

    response = client.post(
        "/calculations",
        json={
            "a": 10.0,
            "b": 5.0,
            "type": operation,
        },
    )

    assert response.status_code == 201
    assert response.json()["type"] == operation
    assert response.json()["result"] == expected


# ============================================================
# INVALID REQUEST VALIDATION
# ============================================================

@pytest.mark.parametrize(
    "payload",
    [
        {"a": 10.0, "b": 0.0, "type": "Divide"},
        {"a": 10.0, "b": 5.0, "type": "Power"},
        {"a": "invalid", "b": 5.0, "type": "Add"},
        {"a": 10.0, "type": "Add"},
        {"a": 10.0, "b": 5.0},
    ],
)
def test_invalid_calculation(client, payload):
    """Invalid calculation requests should return 400."""

    response = client.post(
        "/calculations",
        json=payload,
    )

    assert response.status_code == 400
    assert "error" in response.json()


# ============================================================
# NONEXISTENT CALCULATION
# ============================================================

def test_read_nonexistent_calculation(client):
    """Reading a missing calculation returns 404."""

    response = client.get("/calculations/999999")

    assert response.status_code == 404
    assert response.json()["error"] == "Calculation not found"


def test_update_nonexistent_calculation(client):
    """Updating a missing calculation returns 404."""

    response = client.put(
        "/calculations/999999",
        json=sample_calculation(),
    )

    assert response.status_code == 404


def test_delete_nonexistent_calculation(client):
    """Deleting a missing calculation returns 404."""

    response = client.delete("/calculations/999999")

    assert response.status_code == 404


# ============================================================
# INVALID UPDATE SHOULD PRESERVE SAVED DATA
# ============================================================

def test_invalid_update_preserves_calculation(client):
    """Reject division by zero without changing stored data."""

    created = client.post(
        "/calculations",
        json=sample_calculation(),
    )

    assert created.status_code == 201
    calculation_id = created.json()["id"]

    invalid_update = client.put(
        f"/calculations/{calculation_id}",
        json={
            "a": 20.0,
            "b": 0.0,
            "type": "Divide",
        },
    )

    assert invalid_update.status_code == 400

    # Original calculation must remain unchanged.
    response = client.get(
        f"/calculations/{calculation_id}"
    )

    assert response.status_code == 200
    assert response.json()["type"] == "Add"
    assert response.json()["result"] == 15.0


# ============================================================
# INVALID PATH PARAMETER
# ============================================================

def test_invalid_calculation_id(client):
    """Non-integer calculation IDs should return 400."""

    response = client.get("/calculations/not-a-number")

    assert response.status_code == 400
    assert "error" in response.json()


def test_create_calculation_factory_error(
    client, monkeypatch
):
    """Unexpected calculation ValueError returns 400."""

    def mock_calculate(*args, **kwargs):
        raise ValueError("Calculation failed")

    monkeypatch.setattr(
        CalculationFactory,
        "calculate",
        mock_calculate,
    )

    response = client.post(
        "/calculations",
        json=sample_calculation(),
    )

    assert response.status_code == 400
    assert response.json()["error"] == "Calculation failed"


def test_update_calculation_factory_error(
    client, monkeypatch
):
    """Failed recalculation returns 400."""

    created = client.post(
        "/calculations",
        json=sample_calculation(),
    )

    assert created.status_code == 201
    calculation_id = created.json()["id"]

    def mock_calculate(*args, **kwargs):
        raise ValueError("Update calculation failed")

    monkeypatch.setattr(
        CalculationFactory,
        "calculate",
        mock_calculate,
    )

    response = client.put(
        f"/calculations/{calculation_id}",
        json={
            "a": 20.0,
            "b": 4.0,
            "type": "Divide",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"] == (
        "Update calculation failed"
    )
