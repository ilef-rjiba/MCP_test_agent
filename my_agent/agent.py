"""
Root agent for `adk web`.

Connects to a private Cloud Run MCP gateway over streamable HTTP (with OIDC auth via ADC),
and tracks token usage — input, output, thinking, and cumulative totals across
every model call in a turn.

Run with:
        adk web
        # or, for extra raw per-call metadata in the terminal:
        adk web --log_level DEBUG

Where to see tokens:
    • Terminal   → clean per-call + cumulative log (this file's callback)
    • Browser    → open the "Trace" / "Events" panel on any response;
                   each event shows usage_metadata with per-call token counts
"""

import os
import logging

import google.auth
import google.auth.transport.requests

from google.genai import types
from google.adk.agents import Agent
from google.adk.tools import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse
from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    StreamableHTTPConnectionParams,
)

# ---------------------------------------------------------------------------
# Logging → shows up in the terminal running `adk web`
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("token_monitor")

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"  # required for gemini-3.x models

_MCP_BASE_URL = os.environ.get(
    "MCP_BASE_URL",
    "https://dev-mcp-gateway-api-443216374187.us-central1.run.app",
)

# Fetch the API Key from your environment
_MCP_API_KEY = os.environ.get("MCP_API_KEY", "XXXXX") # Replace with actual API key

# ---------------------------------------------------------------------------
# Per-turn token accumulators (reset when the final answer is produced)
# ---------------------------------------------------------------------------
_totals = {"prompt": 0, "output": 0, "thinking": 0, "total": 0, "calls": 0}


def _reset_totals() -> None:
    for k in _totals:
        _totals[k] = 0


# ---------------------------------------------------------------------------
# Loop guard — blocks a second call to the same tool this turn
# (keyed by tool name only, so different `source=` values are still blocked)
# ---------------------------------------------------------------------------
_tool_calls_this_turn: dict[str, int] = {}
MAX_CALLS_PER_TOOL = 5


def prevent_tool_loops(
    tool: BaseTool,
    args: dict,
    tool_context: ToolContext,
) -> dict | None:
    n = _tool_calls_this_turn.get(tool.name, 0)
    if n >= MAX_CALLS_PER_TOOL:
        return {
            "blocked": True,
            "reason": (
                f"Tool '{tool.name}' was already called this turn. "
                "Do NOT call it again — answer using the result already returned."
            ),
        }
    _tool_calls_this_turn[tool.name] = n + 1
    return None


# ---------------------------------------------------------------------------
# Identity token for the private Cloud Run MCP gateway (via ADC)
# ---------------------------------------------------------------------------
def _get_identity_token() -> str:
    creds, _ = google.auth.default(
        scopes=[
            "openid",
            "email",
            "https://www.googleapis.com/auth/cloud-platform",
        ]
    )
    creds.refresh(google.auth.transport.requests.Request())
    if not getattr(creds, "id_token", None):
        raise RuntimeError(
            "No identity token from ADC. Run: gcloud auth application-default login"
        )
    return creds.id_token


mcp_toolset = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=f"{_MCP_BASE_URL}/mcp",
        headers={
            "Authorization": f"Bearer {_get_identity_token()}",
            "x-api-key": _MCP_API_KEY,
            "Accept": "application/json",
        },
    )
)


# ---------------------------------------------------------------------------
# after_model_callback — fires after EVERY model call (reliable under adk web)
# ---------------------------------------------------------------------------
def track_tokens(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> LlmResponse | None:
    # --- read usage from this call ---
    meta = getattr(llm_response, "usage_metadata", None)
    p = o = th = tot = 0
    if meta:
        p = getattr(meta, "prompt_token_count", 0) or 0
        o = getattr(meta, "candidates_token_count", 0) or 0
        th = getattr(meta, "thoughts_token_count", 0) or 0  # thinking tokens
        tot = getattr(meta, "total_token_count", 0) or 0

        _totals["prompt"] += p
        _totals["output"] += o
        _totals["thinking"] += th
        _totals["total"] += tot
        _totals["calls"] += 1

    # --- inspect this response's parts ---
    text = ""
    has_function_call = False
    content = getattr(llm_response, "content", None)
    if content and content.parts:
        for part in content.parts:
            if getattr(part, "text", None):
                text += part.text
            if getattr(part, "function_call", None):
                has_function_call = True

    # --- skip partial streaming chunks (they lack usage + carry partial text) ---
    if getattr(llm_response, "partial", False):
        return None

    # --- log every complete model call ---
    logger.info(
        "MODEL CALL #%d | in=%d out=%d thinking=%d total=%d | tool_call=%s",
        _totals["calls"],
        p,
        o,
        th,
        tot,
        has_function_call,
    )
    logger.info(
        "  CUMULATIVE this turn → in=%d out=%d thinking=%d TOTAL=%d over %d calls",
        _totals["prompt"],
        _totals["output"],
        _totals["thinking"],
        _totals["total"],
        _totals["calls"],
    )

    # --- only append footer to the FINAL user-facing answer ---
    is_final = bool(text.strip()) and not has_function_call
    if not is_final:
        return None

    footer = (
        f"\n\n---\n"
        f"**Token usage** (this turn · {_totals['calls']} model calls)\n"
        f"- Input: {_totals['prompt']}\n"
        f"- Output: {_totals['output']}\n"
        f"- Thinking: {_totals['thinking']}\n"
        f"- **Total: {_totals['total']}**"
    )

    # rebuild content (assigning to llm_response.text is a silent no-op)
    new_parts = list(content.parts)
    for i in range(len(new_parts) - 1, -1, -1):
        if getattr(new_parts[i], "text", None):
            new_parts[i] = types.Part(text=new_parts[i].text + footer)
            break
    else:
        new_parts.append(types.Part(text=footer))

    llm_response.content = types.Content(role=content.role, parts=new_parts)

    logger.info("TURN COMPLETE → final totals: %s", dict(_totals))

    # reset for next user turn
    _reset_totals()
    _tool_calls_this_turn.clear()

    return llm_response


# ---------------------------------------------------------------------------
# Root agent — `adk web` discovers this automatically
# ---------------------------------------------------------------------------
root_agent = Agent(
    name="test_agent",
    model="gemini-3.5-flash",  # change to gemini-3.5-flash once global endpoint is confirmed
    description="Research agent connected to the private MCP gateway on acn-researchplatform.",
    instruction=(
        "You are a research assistant with access to private MCP retrieval tools.\n\n"
        "PHASE 0: AUTONOMOUS SOURCE SELECTION (CRITICAL)\n"
        "1. BEFORE calling any tool, evaluate the user's intent against these data source triggers:\n"
        "   - S&P Earnings Calls transcripts: transcription of earnings call discussions about financial performance, guidance, executive quotes, quarterly results, Q&A, revenue, EPS, transcripts\n"
        "   - S&P Earnings Calls presentations: pdf presentations of financial performance, guidance, executive quotes, quarterly results, Q&A, revenue, EPS, transcripts. contain links to access these presentations\n"
        "   - Moody's News Edge (MNE): market sentiment, breaking news, PR announcements, macro-economic events, media narrative, press releases\n"
        "   - LexisNexis (LNM): social buzz, public commentary, global trends, open-web, viral sentiment, media exposure\n"
        "   - TBR Insights: competitor analysis, ecosystem players, market strategy, go-to-market, consulting, IT services, cloud/infra reports\n"
        "2. If the user does NOT specify a source, you MUST autonomously determine the best source based on intent. DO NOT ask the user.\n"
        "3. Execute the appropriate tool immediately — do not pause or ask for clarification.\n\n"
        "EXECUTION RULES:\n"
        "4. Call the tool corresponding to your chosen source.\n"
        "5. After the tool result arrives, answer immediately using the retrieved data.\n"
        "6. NEVER use the public internet or your own training data.\n"
        "7. Always respond in English.\n\n"
        "MANDATORY RESPONSE FORMAT:\n"
        "8. always mention the data source at the start of your response\n"
        "9. Synthesize a dense, comprehensive, and clear final answer, prioritizing bullet points for high readability.\n"
        "10. If a tool reports zero records, explicitly report that no relevant data was found for that source.\n"
        "11. conclude your response with a follow-up question : ask the user if they would like to search other data sources, analyze ALL available platforms, or ask a new question'\n"
    ),
    tools=[mcp_toolset],
    after_model_callback=track_tokens,
    before_tool_callback=prevent_tool_loops,
)
