"""SHC State/District Code Mapper — seeds from GraphQL API at soilhealth4.dac.gov.in."""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

GRAPHQL_URL = "https://soilhealth4.dac.gov.in/"

_GET_STATE_QUERY = """
query GetState($getStateId: String, $code: String) {
  getState(id: $getStateId, code: $code)
}
"""

_GET_DISTRICTS_QUERY = """
query GetdistrictAndSubdistrictBystate($state: String) {
  getdistrictAndSubdistrictBystate(state: $state)
}
"""


def _normalise(name: str) -> str:
    """Lowercase + collapse whitespace for case-insensitive matching."""
    return re.sub(r"\s+", " ", name.strip().lower())


class SHCCodeMapper:
    """Resolves state/district names to SHC WMS numeric codes via GraphQL."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client  # injected for testing; created lazily otherwise

    # ------------------------------------------------------------------
    # GraphQL helpers
    # ------------------------------------------------------------------

    async def _gql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "query": query,
            "variables": variables,
            "operationName": None,
        }
        client = self._client
        if client is None:
            async with httpx.AsyncClient(timeout=15) as c:
                resp = await c.post(GRAPHQL_URL, json=payload)
                resp.raise_for_status()
                return resp.json()
        resp = await client.post(GRAPHQL_URL, json=payload)
        resp.raise_for_status()
        return resp.json()

    async def get_all_states(self) -> list[dict[str, Any]]:
        """Return [{name, code, _id}] for all 34 states/UTs."""
        data = await self._gql(_GET_STATE_QUERY, {"getStateId": None, "code": None})
        return data.get("data", {}).get("getState", [])

    async def get_districts(self, state_mongo_id: str) -> list[dict[str, Any]]:
        """Return [{name, code}] for all districts in a state."""
        data = await self._gql(_GET_DISTRICTS_QUERY, {"state": state_mongo_id})
        return data.get("data", {}).get("getdistrictAndSubdistrictBystate", [])

    # ------------------------------------------------------------------
    # DB-backed resolution
    # ------------------------------------------------------------------

    async def resolve(
        self, state_name: str, district_name: str, db: Session
    ) -> tuple[int, int] | None:
        """Case-insensitive lookup. Returns (state_code, district_code) or None."""
        row = db.execute(
            text("""
                SELECT state_code, district_code
                FROM shc_state_district_codes
                WHERE LOWER(state_name) = :state
                  AND LOWER(district_name) = :district
                LIMIT 1
                """),
            {
                "state": _normalise(state_name),
                "district": _normalise(district_name),
            },
        ).fetchone()

        if row is None:
            logger.warning(
                "SHCCodeMapper: no code found for state=%r district=%r",
                state_name,
                district_name,
            )
            return None
        return (row.state_code, row.district_code)

    async def seed_database(self, db: Session) -> int:
        """
        Fetch all states + districts from GraphQL and upsert into
        shc_state_district_codes. Returns total rows inserted/updated.
        """
        states = await self.get_all_states()
        total = 0

        for state in states:
            state_name: str = state.get("name", "")
            state_code: int = int(state.get("code", 0))
            state_id: str = state.get("_id", "")

            try:
                districts = await self.get_districts(state_id)
            except Exception as exc:
                logger.error(
                    "SHCCodeMapper: failed to fetch districts for %s: %s",
                    state_name,
                    exc,
                )
                continue

            for district in districts:
                district_name: str = district.get("name", "")
                district_code: int = int(district.get("code", 0))

                db.execute(
                    text("""
                        INSERT INTO shc_state_district_codes
                            (state_name, state_code, district_name, district_code,
                             created_at, updated_at, enable)
                        VALUES
                            (:sn, :sc, :dn, :dc,
                             NOW(), NOW(), 1)
                        ON CONFLICT (state_code, district_code)
                        DO UPDATE SET
                            state_name    = EXCLUDED.state_name,
                            district_name = EXCLUDED.district_name,
                            updated_at    = NOW()
                        """),
                    {
                        "sn": state_name,
                        "sc": state_code,
                        "dn": district_name,
                        "dc": district_code,
                    },
                )
                total += 1

        db.commit()
        logger.info("SHCCodeMapper: seeded %d state/district rows", total)
        return total
