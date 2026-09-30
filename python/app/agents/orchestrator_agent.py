"""
Root Orchestrator Agent using the Google Antigravity SDK.
Manages user queries and coordinates specialized subagents for agricultural support.
"""

import logging
import uuid
from typing import Optional

try:
    from google.adk import Agent
    from google.adk.runners import InMemoryRunner
    HAS_ADK = True
except (ImportError, ModuleNotFoundError):
    Agent = None
    InMemoryRunner = None
    HAS_ADK = False

try:
    from google.genai import types
except (ImportError, ModuleNotFoundError):
    types = None

from app.agents.agent_tools import (
    get_farm_details,
    get_market_prices,
    get_soil_info,
    get_weather_forecast,
)

logger = logging.getLogger(__name__)


async def run_orchestrator_turn(query: str, farm_id: Optional[int] = None) -> str:
    """
    Invokes the Google Antigravity Root Orchestrator to answer a query.
    If a farm_id is provided, details are automatically fetched and passed as context.
    """
    context = ""
    if farm_id:
        farm_info = get_farm_details(farm_id)
        context = f"Here is the context of the farmer's farm (Farm ID: {farm_id}):\n{farm_info}\n\n"
        logger.info(f"Loaded farm context for orchestrator: {farm_id}")

    if HAS_ADK and Agent and InMemoryRunner and types:
        # Configure the Root Agent via Google ADK
        agent = Agent(
            name="orchestrator",
            instruction=(
                "You are the CropSense Root Orchestrator Agent. Your job is to answer agricultural queries "
                "from Indian farmers. You have access to specialized tools and can spawn subagents "
                "for specific tasks: \n"
                "- Crop Advisory Subagent (for crop selection, variety recommendations, soil suitability)\n"
                "- Pest & Disease Subagent (for diagnosing diseases, treatment options)\n"
                "- Weather Analysis Subagent (for evaluating forecasts and warnings)\n"
                "- Market Intelligence Subagent (for checking prices, matching demand, and booking transport)\n\n"
                "If a query requires deep specialized domain knowledge, delegate it to a subagent by calling "
                "start_subagent with a clear instruction, and compile their outputs into a helpful, structured "
                "response for the farmer in Markdown format. Keep the tone helpful, empathetic, and clear."
            ),
            tools=[get_farm_details, get_soil_info, get_weather_forecast, get_market_prices],
        )

        runner = InMemoryRunner(agent=agent)
        runner.auto_create_session = True

        session_id = f"session_{uuid.uuid4()}"
        new_message = types.Content(parts=[types.Part.from_text(text=f"{context}Query: {query}")])

        response_text = ""
        try:
            async for event in runner.run_async(
                user_id="default_user", session_id=session_id, new_message=new_message
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            response_text += part.text

            if not response_text:
                response_text = (
                    "I processed your request, but did not generate a response. Please check inputs."
                )

            return response_text
        except Exception as e:
            logger.error(f"Orchestrator invocation failed: {e}")
            return f"Sorry, I encountered an error while processing your request: {str(e)}"
    else:
        # Direct Google GenAI Gemini execution (3.8 Flash with 3.5 Flash Lite fallback)
        from app.core.config import settings
        client = None
        for model_name in [settings.GEMINI_MODEL, settings.GEMINI_ASSIST_MODEL, settings.GEMINI_FALLBACK_MODEL]:
            try:
                from google import genai
                if client is None:
                    client = genai.Client()
                prompt = (
                    "You are the CropSense Root Orchestrator Agent. Your job is to answer agricultural queries "
                    "from Indian farmers with helpful, empathetic, structured advice in Markdown.\n\n"
                    f"{context}Query: {query}"
                )
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                logger.warning(f"Model {model_name} invocation failed: {e}. Trying next fallback.")
                continue

        return f"CropSense AI Advisory: Processed query '{query}'."

