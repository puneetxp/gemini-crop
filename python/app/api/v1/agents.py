"""
API endpoints for Google Antigravity Agent orchestration.
Wraps all agent responses with Responsible AI explainability metadata.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.agents.agent_tools import set_agent_user
from app.agents.orchestrator_agent import run_orchestrator_turn
from app.core.dependencies import DB, CurrentUser
from app.services.explainability import wrap_with_explainability

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents", tags=["Agents"])


class AgentQuery(BaseModel):
    query: str
    farm_id: Optional[int] = None


@router.post("/chat", response_model=Dict[str, Any])
async def chat_with_agent(query_data: AgentQuery, current_user: CurrentUser, db: DB):
    """
    Chat with the CropSense Root Orchestrator Agent.
    Delegates to specialized subagents under the hood using the Google Antigravity SDK.

    Response includes **Responsible AI explainability metadata**:
    confidence score, data sources, reasoning chain, limitations, and bias disclosure.
    """
    try:
        # Agent tools read farms / plots only for this user (tool arguments come from the prompt).
        set_agent_user(current_user)
        response_text = await run_orchestrator_turn(
            query=query_data.query, farm_id=query_data.farm_id
        )

        # Detect query type for explainability context
        query_lower = query_data.query.lower()
        if any(w in query_lower for w in ["pest", "disease", "insect", "blight", "fungus"]):
            query_type = "pest_disease"
        elif any(w in query_lower for w in ["price", "market", "mandi", "sell", "buy"]):
            query_type = "market_prices"
        elif any(w in query_lower for w in ["weather", "rain", "forecast", "monsoon"]):
            query_type = "weather"
        elif any(w in query_lower for w in ["cow", "buffalo", "goat", "livestock", "cattle"]):
            query_type = "livestock"
        else:
            query_type = "crop_advisory"

        # Wrap with Responsible AI explainability
        explained_response = wrap_with_explainability(
            response_text=response_text,
            query_type=query_type,
            confidence=0.82,
        )

        return {"success": True, **explained_response}
    except Exception as e:
        logger.error(f"Agent chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
