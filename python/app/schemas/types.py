"""Shared schema types."""

from decimal import Decimal
from typing import Annotated

from pydantic import PlainSerializer

# Validates as Decimal (exact money maths) but serialises to a JSON number. Plain Decimal becomes a
# JSON string in pydantic v2, which breaks number formatting in the frontend (e.g. value.toFixed).
JsonDecimal = Annotated[
    Decimal,
    PlainSerializer(
        lambda v: float(v) if v is not None else None, return_type=float, when_used="json"
    ),
]
