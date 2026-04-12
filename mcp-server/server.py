#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║              Akasha MCP Server v1.2.0                                ║
║                                                                      ║
║  Model Context Protocol server that gives any LLM                    ║
║  (Claude, Gemini, Cursor, Copilot) persistent shared memory          ║
║  via Akasha's Cognitive Fabric.                                      ║
║                                                                      ║
║  Client-side process — runs alongside the LLM client,                ║
║  connects to your Akasha cluster via HTTPS + API Key.                ║
╚══════════════════════════════════════════════════════════════════════╝

Configuration (environment variables):
    AKASHA_URL        Akasha cluster URL (default: https://localhost:7777)
    AKASHA_API_KEY    API key for authentication (required)
    AKASHA_VERIFY_SSL Whether to verify TLS certificates (default: false)

Usage:
    # Run with stdio (Claude Desktop, Cursor)
    python server.py

    # Run with SSE (remote / Windmill)
    python server.py --transport sse --port 8765

    # Interactive dev inspector
    fastmcp dev server.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
from fastmcp import FastMCP

# ─── Configuration ────────────────────────────────────────

AKASHA_URL = os.environ.get("AKASHA_URL", "https://localhost:7777").rstrip("/")
AKASHA_API_KEY = os.environ.get("AKASHA_API_KEY", "")
AKASHA_VERIFY_SSL = os.environ.get("AKASHA_VERIFY_SSL", "false").lower() in ("true", "1", "yes")

# ─── HTTP Client ──────────────────────────────────────────

def _client() -> httpx.Client:
    """Create a configured httpx client for Akasha API calls."""
    headers = {"Content-Type": "application/json"}
    if AKASHA_API_KEY:
        headers["Authorization"] = f"Bearer {AKASHA_API_KEY}"
    return httpx.Client(
        base_url=AKASHA_URL,
        headers=headers,
        verify=AKASHA_VERIFY_SSL,
        timeout=15.0,
    )


def _api_get(path: str, params: dict | None = None) -> dict | list:
    """GET request to Akasha API."""
    with _client() as c:
        r = c.get(path, params=params)
        r.raise_for_status()
        return r.json()


def _api_post(path: str, body: dict) -> dict:
    """POST request to Akasha API."""
    with _client() as c:
        r = c.post(path, json=body)
        r.raise_for_status()
        return r.json()


def _api_delete(path: str) -> dict:
    """DELETE request to Akasha API."""
    with _client() as c:
        r = c.delete(path)
        if r.status_code == 404:
            return {"status": "not_found", "path": path}
        r.raise_for_status()
        return r.json()


# ─── MCP Server ───────────────────────────────────────────

mcp = FastMCP(
    "Akasha",
    instructions=(
        "Akasha — The Shared Cognitive Fabric for Intelligent Agent Systems. "
        "A distributed, real-time shared memory store with 4-layer cognitive architecture "
        "(working → episodic → semantic → procedural), bio-inspired pheromone signaling, "
        "and Nidra consolidation engine. Use these tools to read/write agent memory, "
        "query knowledge, and coordinate multi-agent systems."
    ),
)


# ════════════════════════════════════════════════════════════
#  TOOLS — Actions the LLM can execute
# ════════════════════════════════════════════════════════════


@mcp.tool()
def akasha_read(path: str) -> str:
    """Read a record from Akasha by its exact path.

    Use this to retrieve agent state, memory entries, or any stored data.

    Args:
        path: The record path (e.g. 'agents/my-agent/state', 'memory/semantic/knowledge/topic')
    """
    try:
        data = _api_get(f"/api/v1/records/{path}")
        return json.dumps(data, indent=2, default=str)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return json.dumps({"error": "not_found", "path": path})
        return json.dumps({"error": str(e), "status": e.response.status_code})


@mcp.tool()
def akasha_write(
    path: str,
    value: dict | str | int | float | bool | list,
    tags: Optional[dict[str, str]] = None,
    ttl_seconds: Optional[float] = None,
) -> str:
    """Write a record to Akasha.

    Creates or updates a record at the given path. Use structured paths
    following Akasha conventions:
    - agents/{agent_id}/state — Agent state
    - memory/working/{agent_id}/{key} — Working memory (ephemeral, auto-expires)
    - memory/episodic/{topic}/{event_id} — Episodic memory (task completions)
    - memory/semantic/{domain}/{concept} — Semantic memory (distilled knowledge)
    - memory/procedural/{domain}/{rule} — Procedural memory (learned rules, immutable)
    - shared/{namespace}/{key} — Shared cross-agent data

    Args:
        path: The record path
        value: The data to store (any JSON-serializable value)
        tags: Optional key-value tags for filtering and metadata
        ttl_seconds: Optional time-to-live in seconds (record auto-expires)
    """
    body: dict[str, Any] = {"value": value}
    if tags:
        body["tags"] = tags
    if ttl_seconds is not None:
        body["ttl_seconds"] = ttl_seconds

    try:
        data = _api_post(f"/api/v1/records/{path}", body)
        action = "created" if data.get("version") == 1 else "updated"
        return json.dumps({
            "status": action,
            "path": data["path"],
            "version": data["version"],
        })
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": str(e), "status": e.response.status_code})


@mcp.tool()
def akasha_delete(path: str) -> str:
    """Delete a record from Akasha.

    Args:
        path: The record path to delete
    """
    try:
        data = _api_delete(f"/api/v1/records/{path}")
        return json.dumps(data)
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": str(e), "status": e.response.status_code})


@mcp.tool()
def akasha_query(pattern: str, limit: Optional[int] = None) -> str:
    """Search for records matching a glob pattern.

    Supports single-level (*) and recursive (**) globs:
    - 'agents/*/state' — All agent states
    - 'memory/semantic/**' — All semantic memories
    - 'memory/working/my-agent/*' — All working memory for an agent

    Args:
        pattern: Glob pattern to match against record paths
        limit: Maximum number of results to return
    """
    params: dict[str, Any] = {"pattern": pattern}
    if limit is not None:
        params["limit"] = limit

    try:
        data = _api_get("/api/v1/query", params=params)
        summary = {
            "count": len(data),
            "pattern": pattern,
            "records": [
                {
                    "path": r["path"],
                    "value": r["value"],
                    "version": r.get("version"),
                    "tags": r.get("tags", {}),
                }
                for r in data
            ],
        }
        return json.dumps(summary, indent=2, default=str)
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": str(e), "status": e.response.status_code})


@mcp.tool()
def akasha_memory_store(
    layer: str,
    key: str,
    value: dict | str | int | float | bool | list,
    agent_id: Optional[str] = None,
) -> str:
    """Store data in a specific memory layer.

    Akasha's cognitive architecture has 4 memory layers:
    - working: Short-term, task-specific scratchpad (auto-expires in 30 min)
    - episodic: Medium-term event/task completion history (24h default TTL)
    - semantic: Long-term distilled knowledge (permanent, no TTL)
    - procedural: Learned rules and procedures (permanent, immutable after creation)

    Args:
        layer: Memory layer — one of: working, episodic, semantic, procedural
        key: Key within the layer (e.g. 'current-task', 'analysis-results')
        value: The data to store
        agent_id: Optional agent identifier for scoping (default: 'mcp-agent')
    """
    valid_layers = {"working", "episodic", "semantic", "procedural"}
    if layer not in valid_layers:
        return json.dumps({"error": f"Invalid layer '{layer}'. Must be one of: {valid_layers}"})

    agent = agent_id or "mcp-agent"
    path = f"memory/{layer}/{agent}/{key}"

    ttl_defaults = {
        "working": 30 * 60,      # 30 minutes
        "episodic": 24 * 3600,   # 24 hours
        "semantic": None,        # permanent
        "procedural": None,      # permanent
    }

    tags = {
        "_memory_layer": layer,
        "_agent": agent,
        "_source": "mcp-server",
    }

    body: dict[str, Any] = {"value": value, "tags": tags}
    ttl = ttl_defaults[layer]
    if ttl is not None:
        body["ttl_seconds"] = ttl

    try:
        data = _api_post(f"/api/v1/records/{path}", body)
        return json.dumps({
            "status": "stored",
            "layer": layer,
            "path": data["path"],
            "version": data["version"],
            "ttl_seconds": ttl,
        })
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": str(e), "status": e.response.status_code})


@mcp.tool()
def akasha_memory_recall(
    layer: str,
    pattern: Optional[str] = None,
    agent_id: Optional[str] = None,
) -> str:
    """Recall memories from a specific layer.

    Retrieves all records from a memory layer, optionally filtered by
    agent and/or glob pattern.

    Args:
        layer: Memory layer — one of: working, episodic, semantic, procedural
        pattern: Optional sub-pattern to filter within the layer (e.g. 'task-*')
        agent_id: Optional agent identifier to scope the recall
    """
    valid_layers = {"working", "episodic", "semantic", "procedural"}
    if layer not in valid_layers:
        return json.dumps({"error": f"Invalid layer '{layer}'. Must be one of: {valid_layers}"})

    if agent_id and pattern:
        glob = f"memory/{layer}/{agent_id}/{pattern}"
    elif agent_id:
        glob = f"memory/{layer}/{agent_id}/**"
    elif pattern:
        glob = f"memory/{layer}/**/{pattern}"
    else:
        glob = f"memory/{layer}/**"

    try:
        data = _api_get("/api/v1/query", params={"pattern": glob})
        memories = [
            {
                "path": r["path"],
                "value": r["value"],
                "version": r.get("version"),
                "tags": r.get("tags", {}),
                "updated_at": r.get("updated_at"),
            }
            for r in data
        ]
        return json.dumps({
            "layer": layer,
            "count": len(memories),
            "memories": memories,
        }, indent=2, default=str)
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": str(e), "status": e.response.status_code})


@mcp.tool()
def akasha_pheromone_emit(
    trail: str,
    signal_type: str,
    intensity: float = 0.8,
    payload: Optional[dict] = None,
    half_life_secs: int = 300,
) -> str:
    """Emit a pheromone signal for stigmergic multi-agent coordination.

    Pheromones are volatile signals that decay over time (bio-inspired).
    Other agents can sense them to discover tasks, resources, or warnings.

    Signal types: task_complete, help_needed, resource_found, warning, discovery, available

    Args:
        trail: Trail name — logical channel for the signal (e.g. 'data-pipeline/status')
        signal_type: Type of signal (task_complete, help_needed, warning, etc.)
        intensity: Signal strength 0.0-1.0 (higher = more important)
        payload: Optional structured data attached to the signal
        half_life_secs: How quickly the signal decays (seconds, default 300)
    """
    body = {
        "trail": trail,
        "signal_type": signal_type,
        "emitter": "mcp-agent",
        "intensity": min(max(intensity, 0.0), 1.0),
        "half_life_secs": half_life_secs,
    }
    if payload:
        body["payload"] = payload

    try:
        data = _api_post("/api/v1/pheromones", body)
        return json.dumps({"status": "emitted", "trail": trail, "signal_type": signal_type})
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": str(e), "status": e.response.status_code})


@mcp.tool()
def akasha_pheromone_sense() -> str:
    """Sense all active pheromone signals in the environment.

    Returns all pheromone trails with their current intensity,
    emitter, and payload. Use this to discover what other agents
    are doing, find available resources, or detect warnings.
    """
    try:
        data = _api_get("/api/v1/pheromones")
        signals = [
            {
                "trail": p.get("trail"),
                "signal_type": p.get("signal_type"),
                "emitter": p.get("emitter"),
                "intensity": p.get("intensity"),
                "payload": p.get("payload"),
            }
            for p in data
        ]
        return json.dumps({
            "count": len(signals),
            "signals": signals,
        }, indent=2, default=str)
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": str(e), "status": e.response.status_code})


@mcp.tool()
def akasha_health() -> str:
    """Get the health status of the Akasha cluster.

    Returns version, node count, encryption status, cluster mode,
    and record count.
    """
    try:
        data = _api_get("/api/v1/health")
        cluster = data.get("cluster", {})
        encryption = data.get("encryption", {})
        return json.dumps({
            "status": data.get("status"),
            "version": data.get("version"),
            "records": data.get("records"),
            "cluster": {
                "mode": cluster.get("mode", "standalone"),
                "nodes": cluster.get("peers_alive", 1),
                "role": cluster.get("role", "standalone"),
            },
            "encryption": {
                "enabled": encryption.get("enabled", False),
                "algorithm": encryption.get("algorithm", "none"),
            },
        }, indent=2)
    except httpx.HTTPError as e:
        return json.dumps({"error": f"Cluster unreachable: {e}"})


@mcp.tool()
def akasha_agents() -> str:
    """List all registered agents and their current state.

    Returns agent IDs, paths, and their latest state data.
    """
    try:
        data = _api_get("/api/v1/agents")
        return json.dumps({
            "count": len(data),
            "agents": data,
        }, indent=2, default=str)
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": str(e), "status": e.response.status_code})


@mcp.tool()
def akasha_nidra_sweep() -> str:
    """Force an immediate Nidra consolidation cycle.

    Nidra is Akasha's background consolidation engine (like sleep for memory).
    This triggers an immediate sweep that:
    1. Evaporates decayed pheromones
    2. Counts records per memory layer
    3. Consolidates episodic memory into semantic knowledge (if thresholds are met)

    Returns a NidraReport with cycle results.
    """
    try:
        data = _api_post("/api/v1/nidra/sweep", {})
        return json.dumps({
            "status": "sweep_complete",
            "cycle": data.get("cycle"),
            "pheromones_evaporated": data.get("pheromones_evaporated"),
            "patterns_extracted": data.get("patterns_extracted"),
            "total_records": data.get("total_records"),
            "layer_counts": data.get("layer_counts", {}),
        }, indent=2)
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": str(e), "status": e.response.status_code})


@mcp.tool()
def akasha_diagnostics() -> str:
    """Run a comprehensive diagnostic report on the Akasha cluster.

    Returns a full system health assessment including:
    - Health score (0-100) with traffic-light signal (🟢🟡🔴)
    - Cluster topology (nodes, versions, Raft status)
    - Data consistency (CRDT pending deltas, tracked paths)
    - Performance metrics (reads, writes, queries, system resources)
    - Memory layer distribution (working, episodic, semantic, procedural)
    - Security posture (encryption, TLS, license, namespace policies)
    - Nidra consolidation engine status
    - Findings with severity and recommendations
    - Full Markdown report for sharing/export

    Requires admin-level API key.
    """
    try:
        data = _api_get("/api/v1/diag/report")
        return json.dumps({
            "health_score": data.get("health_score"),
            "health_signal": data.get("health_signal"),
            "version": data.get("version"),
            "timestamp": data.get("timestamp"),
            "topology": data.get("topology"),
            "performance": data.get("performance"),
            "memory": data.get("memory"),
            "security": data.get("security"),
            "findings": data.get("findings"),
            "markdown": data.get("markdown"),
        }, indent=2, default=str)
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": str(e), "status": e.response.status_code})


# ════════════════════════════════════════════════════════════
#  RESOURCES — Data the LLM can read via URI
# ════════════════════════════════════════════════════════════


@mcp.resource("akasha://health")
def resource_health() -> str:
    """Current health status of the Akasha cluster."""
    try:
        data = _api_get("/api/v1/health")
        return json.dumps(data, indent=2, default=str)
    except httpx.HTTPError as e:
        return json.dumps({"error": str(e)})


@mcp.resource("akasha://memory/layers")
def resource_memory_layers() -> str:
    """Memory layer statistics — record counts per cognitive layer."""
    try:
        data = _api_get("/api/v1/memory/layers")
        return json.dumps(data, indent=2, default=str)
    except httpx.HTTPError as e:
        return json.dumps({"error": str(e)})


@mcp.resource("akasha://records/{path}")
def resource_record(path: str) -> str:
    """Read any Akasha record by its path."""
    try:
        data = _api_get(f"/api/v1/records/{path}")
        return json.dumps(data, indent=2, default=str)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return json.dumps({"error": "not_found", "path": path})
        return json.dumps({"error": str(e)})


@mcp.resource("akasha://agents/{agent_id}")
def resource_agent(agent_id: str) -> str:
    """Read the current state of a specific agent."""
    try:
        data = _api_get(f"/api/v1/records/agents/{agent_id}/state")
        return json.dumps(data, indent=2, default=str)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return json.dumps({"error": "agent_not_found", "agent_id": agent_id})
        return json.dumps({"error": str(e)})


@mcp.resource("akasha://tree")
def resource_tree() -> str:
    """Full tree snapshot — all record paths and their values."""
    try:
        data = _api_get("/api/v1/tree")
        return json.dumps({
            "total_paths": len(data),
            "paths": sorted(data.keys()) if isinstance(data, dict) else data,
        }, indent=2, default=str)
    except httpx.HTTPError as e:
        return json.dumps({"error": str(e)})


@mcp.resource("akasha://diagnostics")
def resource_diagnostics() -> str:
    """Full diagnostic report including health score and cluster analysis."""
    try:
        data = _api_get("/api/v1/diag/report")
        return data.get("markdown", json.dumps(data, indent=2, default=str))
    except httpx.HTTPError as e:
        return json.dumps({"error": str(e)})


# ════════════════════════════════════════════════════════════
#  PROMPTS — Reusable prompt templates
# ════════════════════════════════════════════════════════════


@mcp.prompt()
def memory_consolidation(agent_id: str = "mcp-agent") -> str:
    """Analyze episodic memories and generate a semantic summary.

    Simulates Nidra's consolidation: reads all episodic events for an agent,
    identifies patterns, and produces a distilled knowledge summary.
    """
    return f"""You are acting as Akasha's Nidra consolidation engine.

Your task:
1. Use akasha_memory_recall with layer="episodic" and agent_id="{agent_id}" to retrieve all episodic memories
2. Analyze the events for patterns, success rates, recurring issues, and key learnings
3. Synthesize a concise semantic summary capturing the distilled knowledge
4. Use akasha_memory_store with layer="semantic" to persist the consolidated knowledge
5. Optionally, suggest which episodic records can be archived (but do NOT delete them without confirmation)

Focus on extracting:
- Success/failure patterns and their causes
- Optimal parameters or configurations discovered
- Recurring problems and their solutions
- Performance trends over time

Format the semantic summary as structured JSON with fields:
  concept, summary, confidence, source_episodes, patterns, recommendations
"""


@mcp.prompt()
def agent_status_report() -> str:
    """Generate a comprehensive status report of all agents in the system."""
    return """You are generating an Akasha system status report.

Your task:
1. Use akasha_health to check the cluster status
2. Use akasha_agents to list all registered agents
3. Use akasha_pheromone_sense to check active signals
4. Use akasha_memory_recall with layer="working" to see active tasks
5. Use the akasha://memory/layers resource to get memory distribution

Generate a structured report covering:
- Cluster health (version, nodes, encryption)
- Active agents and their current tasks
- Memory distribution across layers
- Active pheromone signals (coordination state)
- Any anomalies or concerns

Format the report in clear markdown with sections and tables.
"""


@mcp.prompt()
def system_health_check() -> str:
    """Run a diagnostic health check of the Akasha cluster."""
    return """You are performing a diagnostic health check of the Akasha cluster.

Your task:
1. Use akasha_diagnostics to get a comprehensive diagnostic report
2. Review the health score and findings
3. If the score is below 100, investigate each finding
4. Verify data access with akasha_query pattern="**" limit=3
5. Check the pheromone subsystem with akasha_pheromone_sense

Report:
- Overall health score and signal
- Node status (alive/dead/suspect)
- Memory distribution across layers
- Active warnings and their severity
- Security posture (encryption, TLS, license)
- Recommendations for improvement

If any check fails, explain the likely cause and suggest remediation.
"""


@mcp.prompt()
def knowledge_extraction(topic: str = "general") -> str:
    """Extract and organize knowledge from Akasha records on a topic."""
    return f"""You are a knowledge extraction specialist working with Akasha.

Your task:
1. Use akasha_query to search for records related to "{topic}" across all namespaces:
   - Try pattern "memory/semantic/**" for existing knowledge
   - Try pattern "memory/episodic/**" for recent events
   - Try pattern "memory/procedural/**" for established rules
2. Analyze all found records and organize the knowledge
3. Identify gaps — what's missing that should be documented?
4. Generate a structured knowledge base entry

Store the extracted knowledge using akasha_memory_store with:
- layer="semantic"
- key="knowledge/{topic}"
- Include confidence scores and source references

The output should be a well-organized knowledge summary that future agents can use.
"""


# ════════════════════════════════════════════════════════════
#  ENTRYPOINT
# ════════════════════════════════════════════════════════════

def main():
    """Run the Akasha MCP server."""
    # Validate configuration
    if not AKASHA_API_KEY:
        print(
            "⚠️  AKASHA_API_KEY not set. The server will try unauthenticated access.\n"
            "   Generate a key: curl -sk -X POST https://host:7777/api/v1/admin/keys \\\n"
            "     -H 'Authorization: Bearer <jwt>' \\\n"
            "     -d '{\"name\":\"mcp-server\",\"namespaces\":[\"**\"],\"role\":\"agent\"}'",
            file=sys.stderr,
        )

    # Check connectivity
    try:
        health = _api_get("/api/v1/health")
        version = health.get("version", "?")
        nodes = health.get("cluster", {}).get("peers_alive", 1)
        enc = "🔒" if health.get("encryption", {}).get("enabled") else "🔓"
        print(
            f"✅ Connected to Akasha v{version} ({nodes} nodes) {enc}",
            file=sys.stderr,
        )
    except Exception as e:
        print(f"⚠️  Cannot reach Akasha at {AKASHA_URL}: {e}", file=sys.stderr)
        print("   The server will start anyway — tools will fail until Akasha is reachable.", file=sys.stderr)

    mcp.run()


if __name__ == "__main__":
    main()
