# Akasha — Agent Integration Guide

> How to connect the most popular AI agent frameworks to Akasha's shared cognitive fabric.

**Akasha Version**: 1.0.4  
**Last Updated**: 2026-04-07

---

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [Pi (Coding Agent)](#1-pi-coding-agent) ← You are here
3. [LangGraph](#2-langgraph)
4. [CrewAI](#3-crewai)
5. [AutoGen / AG2](#4-autogen--ag2)
6. [OpenAI Agents SDK](#5-openai-agents-sdk)
7. [Google ADK (Agent Development Kit)](#6-google-adk)
8. [Semantic Kernel](#7-semantic-kernel)
9. [Claude Code / Anthropic Tool Use](#8-claude-code--anthropic-tool-use)
10. [Smolagents (Hugging Face)](#9-smolagents-hugging-face)
11. [Dify / n8n (Low-Code)](#10-dify--n8n-low-code)
12. [Real-Time Subscription (All Frameworks)](#real-time-subscription)
13. [Pheromone Coordination Pattern](#pheromone-coordination)

---

## Quick Reference

```
Akasha URL:      https://your-akasha-host:7777
Auth:            Authorization: Bearer <token>  OR  Authorization: Bearer ak_<api-key>
API Prefix:      /api/v1
WebSocket:       wss://your-akasha-host:7777/api/v1/stream?pattern=**
Python SDK:      pip install git+https://github.com/ocuil/akasha-public.git#subdirectory=sdks/python
Content-Type:    application/json
TLS:             Required (self-signed certs supported)
```

### Core Endpoints

| Action | Method | Endpoint | Body |
|--------|--------|----------|------|
| Store memory | `POST` | `/api/v1/records/{path}` | `{"data": "...", "ttl_secs": 300}` |
| Read memory | `GET` | `/api/v1/records/{path}` | — |
| Query (glob) | `GET` | `/api/v1/query?pattern=agents/**` | — |
| Delete | `DELETE` | `/api/v1/records/{path}` | — |
| Emit pheromone | `POST` | `/api/v1/pheromones` | `{"trail": "...", "signal_type": "...", "intensity": 0.9}` |
| Read pheromone | `GET` | `/api/v1/pheromones/{trail}` | — |
| Health | `GET` | `/api/v1/health` | — |
| Stream (WS) | `GET` | `/api/v1/stream?pattern=**` | WebSocket upgrade |

### Memory Path Convention

```
memory/
├── working/{agent-id}/       # Short-lived task state (TTL: 300s)
├── episodic/{agent-id}/      # Session logs and events
├── semantic/{domain}/        # Permanent shared knowledge
└── procedural/{capability}/  # Reusable workflows
```

---

## 1. Pi (Coding Agent)

**What**: Terminal-based coding agent with file read/write, bash, and extensible skills.  
**Stars**: 32.8k | **Language**: TypeScript | **Install**: `npm install -g @mariozechner/pi-coding-agent`  
**Docs**: [pi.dev](https://pi.dev) | [GitHub](https://github.com/badlogic/pi-mono)

### How Pi Works with Akasha

Pi has native `bash` tool access, making Akasha integration trivial via `curl`. The best approach is to give Pi a system prompt (via `.pi/agent/instructions.md` or project-level `.pi/instructions.md`) that teaches it to use Akasha.

### Step 1: Create `.pi/instructions.md` in your project

```markdown
## Akasha Memory Integration

You have access to a shared memory system called Akasha. Use it to persist knowledge
across sessions and coordinate with other agents.

### Connection
- URL: https://localhost:7777
- Token: <YOUR_API_KEY>
- Always use: `curl -sk` (self-signed TLS)

### Store Knowledge (after completing a task)
```bash
curl -sk -X POST https://localhost:7777/api/v1/records/memory/semantic/codebase/{topic} \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"data": "<summary of what you learned>"}'
```

### Recall Knowledge (before starting a task)
```bash
curl -sk https://localhost:7777/api/v1/query?pattern=memory/semantic/codebase/** \
  -H "Authorization: Bearer <TOKEN>"
```

### Save Current Task State
```bash
curl -sk -X POST https://localhost:7777/api/v1/records/memory/working/pi/current-task \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"data": "<what you are working on>", "ttl_secs": 1800}'
```

### Signal Other Agents
```bash
curl -sk -X POST https://localhost:7777/api/v1/pheromones \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"trail": "tasks/code-review", "signal_type": "request", "message": "PR #42 ready for review", "intensity": 0.8}'
```

### Rules
1. Before starting any task, query Akasha for relevant prior knowledge
2. After completing a task, store a concise summary of what changed and why
3. Keep your working memory updated with TTL so it auto-expires
4. Use pheromones to signal when you need help or when a task is done
```

### Step 2: Use Pi with Akasha

```bash
# Start pi in your project (it reads .pi/instructions.md automatically)
pi

# Pi now has Akasha context. Ask it:
> "Check Akasha for any prior knowledge about our auth module before refactoring"
> "Store what you learned about the database schema in Akasha"
> "Signal the research agent that the API endpoint is ready"
```

### Advanced: Pi Skill Package (npm)

For a richer integration, create a Pi skill package:

```bash
# Install as a Pi skill
pi install git:github.com/ocuil/akasha-public
```

Then use via `/akasha:store`, `/akasha:recall`, `/akasha:signal` slash commands within Pi.

---

## 2. LangGraph

**What**: Stateful, graph-based agent orchestration (production standard).  
**By**: LangChain | **Language**: Python/JS | **Install**: `pip install langgraph`

### Integration Pattern

LangGraph agents use **tools**. Create Akasha tools that the agent can invoke at each graph node.

```python
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
import httpx

AKASHA_URL = "https://localhost:7777"
AKASHA_TOKEN = "ak_your_api_key"
HEADERS = {"Authorization": f"Bearer {AKASHA_TOKEN}", "Content-Type": "application/json"}

@tool
def akasha_store(path: str, data: str, ttl_secs: int = 0) -> str:
    """Store knowledge in Akasha shared memory. Path format: memory/semantic/{domain}/{topic}"""
    body = {"data": data}
    if ttl_secs > 0:
        body["ttl_secs"] = ttl_secs
    r = httpx.post(f"{AKASHA_URL}/api/v1/records/{path}", json=body, headers=HEADERS, verify=False)
    return f"Stored at {path}" if r.status_code < 300 else f"Error: {r.text}"

@tool
def akasha_recall(pattern: str) -> str:
    """Query Akasha shared memory. Use glob patterns like memory/semantic/research/**"""
    r = httpx.get(f"{AKASHA_URL}/api/v1/query", params={"pattern": pattern}, headers=HEADERS, verify=False)
    return r.text if r.status_code == 200 else f"Error: {r.text}"

@tool
def akasha_signal(trail: str, signal_type: str, message: str, intensity: float = 0.8) -> str:
    """Emit a pheromone signal to coordinate with other agents."""
    body = {"trail": trail, "signal_type": signal_type, "message": message, "intensity": intensity}
    r = httpx.post(f"{AKASHA_URL}/api/v1/pheromones", json=body, headers=HEADERS, verify=False)
    return f"Signal emitted on {trail}" if r.status_code < 300 else f"Error: {r.text}"

# Create agent with Akasha tools
agent = create_react_agent(
    model="openai:gpt-4o",
    tools=[akasha_store, akasha_recall, akasha_signal],
    prompt="You are a research agent. Use Akasha to store findings and coordinate with peers."
)
```

### Reactive LangGraph Node (WebSocket)

```python
import asyncio, websockets, json

async def akasha_listener(graph_invoke):
    """Continuously listen to Akasha events and trigger graph runs."""
    uri = f"wss://localhost:7777/api/v1/stream?pattern=memory/semantic/**"
    headers = {"Authorization": f"Bearer {AKASHA_TOKEN}"}
    async with websockets.connect(uri, additional_headers=headers, ssl=False) as ws:
        async for message in ws:
            event = json.loads(message)
            if event["kind"] == "Created":
                # Trigger the LangGraph agent with the new knowledge
                await graph_invoke({"input": f"New knowledge detected: {event['path']}"})
```

---

## 3. CrewAI

**What**: Role-based multi-agent framework for rapid prototyping.  
**Install**: `pip install crewai crewai-tools`

```python
from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
import httpx

AKASHA = "https://localhost:7777"
TOKEN = "ak_your_key"
H = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

class AkashaStoreTool(BaseTool):
    name: str = "Store in Akasha"
    description: str = "Store knowledge in shared memory. Args: path (str), data (str)"

    def _run(self, path: str, data: str) -> str:
        r = httpx.post(f"{AKASHA}/api/v1/records/{path}", json={"data": data}, headers=H, verify=False)
        return f"✅ Stored at {path}" if r.status_code < 300 else f"❌ {r.text}"

class AkashaRecallTool(BaseTool):
    name: str = "Recall from Akasha"
    description: str = "Query shared memory. Args: pattern (str) — use globs like memory/semantic/**"

    def _run(self, pattern: str) -> str:
        r = httpx.get(f"{AKASHA}/api/v1/query", params={"pattern": pattern}, headers=H, verify=False)
        return r.text if r.status_code == 200 else f"❌ {r.text}"

# Multi-agent crew with shared Akasha memory
researcher = Agent(
    role="Research Analyst",
    goal="Find and store insights in Akasha shared memory",
    tools=[AkashaStoreTool(), AkashaRecallTool()],
    verbose=True
)

writer = Agent(
    role="Content Writer",
    goal="Read research from Akasha and write reports",
    tools=[AkashaRecallTool()],
    verbose=True
)

crew = Crew(
    agents=[researcher, writer],
    tasks=[
        Task(description="Research AI trends and store in Akasha", agent=researcher),
        Task(description="Read research from Akasha and write summary", agent=writer),
    ]
)
crew.kickoff()
```

---

## 4. AutoGen / AG2

**What**: Multi-agent conversational framework.  
**Install**: `pip install autogen-agentchat`

```python
from autogen import AssistantAgent, UserProxyAgent, register_function
import httpx

AKASHA = "https://localhost:7777"
H = {"Authorization": "Bearer ak_your_key", "Content-Type": "application/json"}

def store_memory(path: str, data: str) -> str:
    """Store data in Akasha shared memory at the given path."""
    r = httpx.post(f"{AKASHA}/api/v1/records/{path}", json={"data": data}, headers=H, verify=False)
    return "Stored" if r.status_code < 300 else f"Error: {r.text}"

def recall_memory(pattern: str) -> str:
    """Recall data from Akasha. Use glob patterns like memory/semantic/**"""
    r = httpx.get(f"{AKASHA}/api/v1/query", params={"pattern": pattern}, headers=H, verify=False)
    return r.text

assistant = AssistantAgent(
    "akasha_agent",
    system_message="You have access to Akasha shared memory. Use store_memory to save knowledge and recall_memory to retrieve it.",
    llm_config={"model": "gpt-4o"}
)

user_proxy = UserProxyAgent("user", human_input_mode="NEVER", code_execution_config=False)

register_function(store_memory, caller=assistant, executor=user_proxy,
    name="store_memory", description="Store data in Akasha shared memory")
register_function(recall_memory, caller=assistant, executor=user_proxy,
    name="recall_memory", description="Query Akasha shared memory with glob patterns")

user_proxy.initiate_chat(assistant, message="Research quantum computing and store your findings in Akasha")
```

---

## 5. OpenAI Agents SDK

**What**: Lightweight official SDK for building OpenAI-native agents.  
**Install**: `pip install openai-agents`

```python
from agents import Agent, Runner, function_tool
import httpx

AKASHA = "https://localhost:7777"
H = {"Authorization": "Bearer ak_your_key", "Content-Type": "application/json"}

@function_tool
def store_knowledge(path: str, data: str) -> str:
    """Store knowledge in Akasha shared memory. Use paths like memory/semantic/domain/topic"""
    r = httpx.post(f"{AKASHA}/api/v1/records/{path}", json={"data": data}, headers=H, verify=False)
    return f"Stored at {path}" if r.status_code < 300 else f"Error: {r.text}"

@function_tool
def recall_knowledge(pattern: str) -> str:
    """Query Akasha shared memory. Use glob patterns like memory/semantic/**"""
    r = httpx.get(f"{AKASHA}/api/v1/query", params={"pattern": pattern}, headers=H, verify=False)
    return r.text if r.status_code == 200 else f"Error: {r.text}"

agent = Agent(
    name="Researcher",
    instructions="You are a research agent. Store findings in Akasha and recall prior knowledge before starting tasks.",
    tools=[store_knowledge, recall_knowledge],
)

result = Runner.run_sync(agent, "What do we already know about API security? Check Akasha first, then research.")
print(result.final_output)
```

---

## 6. Google ADK

**What**: Agent Development Kit for Gemini-native agents.  
**Install**: `pip install google-adk`

```python
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
import httpx

AKASHA = "https://localhost:7777"
H = {"Authorization": "Bearer ak_your_key", "Content-Type": "application/json"}

def akasha_store(path: str, data: str) -> dict:
    """Store knowledge in Akasha. Path: memory/semantic/{domain}/{topic}"""
    r = httpx.post(f"{AKASHA}/api/v1/records/{path}", json={"data": data}, headers=H, verify=False)
    return {"status": "ok", "path": path} if r.status_code < 300 else {"error": r.text}

def akasha_recall(pattern: str) -> dict:
    """Query Akasha memory. Pattern: memory/semantic/** for all knowledge."""
    r = httpx.get(f"{AKASHA}/api/v1/query", params={"pattern": pattern}, headers=H, verify=False)
    return r.json() if r.status_code == 200 else {"error": r.text}

agent = Agent(
    name="akasha_researcher",
    model="gemini-2.0-flash",
    instruction="Use Akasha to persist and share knowledge across sessions.",
    tools=[FunctionTool(akasha_store), FunctionTool(akasha_recall)],
)
```

---

## 7. Semantic Kernel

**What**: Enterprise-grade AI orchestration by Microsoft.  
**Install**: `pip install semantic-kernel` or NuGet: `Microsoft.SemanticKernel`

```python
from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function
import httpx

AKASHA = "https://localhost:7777"
H = {"Authorization": "Bearer ak_your_key", "Content-Type": "application/json"}

class AkashaPlugin:
    @kernel_function(name="store", description="Store knowledge in Akasha shared memory")
    def store(self, path: str, data: str) -> str:
        r = httpx.post(f"{AKASHA}/api/v1/records/{path}", json={"data": data}, headers=H, verify=False)
        return f"Stored at {path}" if r.status_code < 300 else f"Error: {r.text}"

    @kernel_function(name="recall", description="Query Akasha shared memory with glob patterns")
    def recall(self, pattern: str) -> str:
        r = httpx.get(f"{AKASHA}/api/v1/query", params={"pattern": pattern}, headers=H, verify=False)
        return r.text

kernel = Kernel()
kernel.add_plugin(AkashaPlugin(), "akasha")
```

---

## 8. Claude Code / Anthropic Tool Use

**What**: Anthropic's coding agent with native tool calling.  
**Also applies to**: Any agent using Anthropic's Messages API with tools.

### Via MCP Server

Create an Akasha MCP server that Claude Code can use:

```python
# akasha_mcp_server.py
from mcp.server.fastmcp import FastMCP
import httpx

AKASHA = "https://localhost:7777"
H = {"Authorization": "Bearer ak_your_key", "Content-Type": "application/json"}

mcp = FastMCP("akasha")

@mcp.tool()
def store_memory(path: str, data: str, ttl_secs: int = 0) -> str:
    """Store knowledge in Akasha shared memory. Path format: memory/semantic/{domain}/{topic}"""
    body = {"data": data}
    if ttl_secs > 0:
        body["ttl_secs"] = ttl_secs
    r = httpx.post(f"{AKASHA}/api/v1/records/{path}", json=body, headers=H, verify=False)
    return f"Stored at {path}" if r.status_code < 300 else f"Error: {r.text}"

@mcp.tool()
def recall_memory(pattern: str = "memory/semantic/**") -> str:
    """Query Akasha shared memory. Use glob patterns like memory/semantic/codebase/**"""
    r = httpx.get(f"{AKASHA}/api/v1/query", params={"pattern": pattern}, headers=H, verify=False)
    return r.text if r.status_code == 200 else f"Error: {r.text}"

@mcp.tool()
def emit_signal(trail: str, signal_type: str, message: str) -> str:
    """Emit a pheromone signal to coordinate with other agents."""
    body = {"trail": trail, "signal_type": signal_type, "message": message, "intensity": 0.8}
    r = httpx.post(f"{AKASHA}/api/v1/pheromones", json=body, headers=H, verify=False)
    return f"Signal emitted: {trail}" if r.status_code < 300 else f"Error: {r.text}"

if __name__ == "__main__":
    mcp.run()
```

Add to Claude Code config (`~/.claude/mcp.json`):
```json
{
  "mcpServers": {
    "akasha": {
      "command": "uv",
      "args": ["run", "/path/to/akasha_mcp_server.py"]
    }
  }
}
```

---

## 9. Smolagents (Hugging Face)

**What**: Lightweight agent framework by Hugging Face.  
**Install**: `pip install smolagents`

```python
from smolagents import CodeAgent, tool, HfApiModel
import httpx

AKASHA = "https://localhost:7777"
H = {"Authorization": "Bearer ak_your_key", "Content-Type": "application/json"}

@tool
def store_in_akasha(path: str, data: str) -> str:
    """Store knowledge in Akasha shared memory for other agents to access.
    Args:
        path: Memory path like memory/semantic/research/quantum
        data: The knowledge to store (text)
    """
    r = httpx.post(f"{AKASHA}/api/v1/records/{path}", json={"data": data}, headers=H, verify=False)
    return f"Stored at {path}" if r.status_code < 300 else f"Error: {r.text}"

@tool
def recall_from_akasha(pattern: str) -> str:
    """Query shared memory from Akasha. Use glob patterns.
    Args:
        pattern: Glob pattern like memory/semantic/** or memory/semantic/research/*
    """
    r = httpx.get(f"{AKASHA}/api/v1/query", params={"pattern": pattern}, headers=H, verify=False)
    return r.text if r.status_code == 200 else f"Error: {r.text}"

agent = CodeAgent(
    tools=[store_in_akasha, recall_from_akasha],
    model=HfApiModel("Qwen/Qwen2.5-72B-Instruct"),
)
agent.run("Check if we have any prior research in Akasha, then investigate AI regulations")
```

---

## 10. Dify / n8n (Low-Code)

**What**: No-code/low-code agent platforms with HTTP request nodes.

### Dify

1. Create a **Tool** → **Custom Tool** → **API-based**
2. OpenAPI spec:

```yaml
openapi: "3.0.0"
info:
  title: Akasha Memory
  version: "1.0.4"
servers:
  - url: https://your-akasha-host:7777/api/v1
paths:
  /records/{path}:
    post:
      operationId: storeMemory
      parameters:
        - name: path
          in: path
          required: true
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                data:
                  type: string
      security:
        - bearer: []
  /query:
    get:
      operationId: recallMemory
      parameters:
        - name: pattern
          in: query
          schema:
            type: string
            default: "memory/semantic/**"
      security:
        - bearer: []
```

### n8n

Use an **HTTP Request** node:
- **Method**: POST
- **URL**: `https://your-host:7777/api/v1/records/memory/semantic/{{$node.topic}}`
- **Authentication**: Header Auth → `Authorization: Bearer ak_your_key`
- **Body**: `{"data": "{{$node.output}}"}`

---

## Real-Time Subscription

All frameworks can use WebSocket for push-based reactivity:

```python
import asyncio, websockets, json, ssl

AKASHA_WS = "wss://localhost:7777/api/v1/stream"
HEADERS = {"Authorization": "Bearer ak_your_key"}

async def listen(pattern="**", on_event=None):
    """Subscribe to Akasha events in real time."""
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    async with websockets.connect(
        f"{AKASHA_WS}?pattern={pattern}",
        additional_headers=HEADERS,
        ssl=ssl_ctx
    ) as ws:
        async for msg in ws:
            event = json.loads(msg)
            if on_event:
                await on_event(event)

# Example: react to new semantic memories
async def handle(event):
    print(f"[{event['kind']}] {event['path']}")
    if event["kind"] == "Created" and "security" in event["path"]:
        print("⚠️ Security finding detected — triggering response agent")

asyncio.run(listen(pattern="memory/semantic/**", on_event=handle))
```

### Event Types

| Event | When | Use Case |
|-------|------|----------|
| `Created` | New record stored | New knowledge, task assignments |
| `Updated` | Record modified | Status changes, progress |
| `Deleted` | Record removed | Task cancellation |
| `Expired` | TTL elapsed | Working memory cleanup |
| `AgentRegistered` | Agent connected | Team composition change |
| `AgentLost` | Agent offline | Failover, work redistribution |

---

## Pheromone Coordination

Prevent duplicate work across agents with pheromone signals:

```python
import httpx

AKASHA = "https://localhost:7777"
H = {"Authorization": "Bearer ak_your_key", "Content-Type": "application/json"}

def claim_task(task_id: str, agent_name: str) -> bool:
    """Try to claim a task. Returns False if another agent already claimed it."""
    # Check if someone else is working on it
    r = httpx.get(f"{AKASHA}/api/v1/pheromones/tasks/{task_id}", headers=H, verify=False)
    if r.status_code == 200:
        trail = r.json()
        if trail.get("intensity", 0) > 0.3 and trail.get("signal_type") == "claim":
            return False  # Another agent is on it

    # Claim it
    httpx.post(f"{AKASHA}/api/v1/pheromones", headers=H, verify=False, json={
        "trail": f"tasks/{task_id}",
        "signal_type": "claim",
        "message": f"Claimed by {agent_name}",
        "intensity": 0.9,
        "half_life_secs": 1800  # Expires in 30 min if not renewed
    })
    return True

def complete_task(task_id: str, result: str):
    """Signal task completion via pheromone."""
    httpx.post(f"{AKASHA}/api/v1/pheromones", headers=H, verify=False, json={
        "trail": f"tasks/{task_id}",
        "signal_type": "complete",
        "message": result,
        "intensity": 1.0,
        "half_life_secs": 3600
    })
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Akasha Cluster (3 nodes)                 │
│  ┌──────────┬──────────┬──────────┬──────────┬───────────┐  │
│  │ Records  │ Pheromones│ Nidra   │  CRDT    │ WebSocket │  │
│  │ (Memory) │ (Signals) │ (Consol)│ (Sync)  │ (Stream)  │  │
│  └────┬─────┴────┬─────┴────┬────┴────┬────┴─────┬─────┘  │
│       │          │          │         │          │          │
│  REST API  ·  gRPC  ·  WebSocket  ·  Python SDK           │
└───────┼──────────┼──────────┼─────────┼──────────┼─────────┘
        │          │          │         │          │
   ┌────┴────┐ ┌───┴───┐ ┌───┴───┐ ┌──┴───┐ ┌───┴─────┐
   │   Pi    │ │ Lang  │ │ Crew  │ │Claude│ │ AutoGen │
   │ (bash)  │ │ Graph │ │  AI   │ │ Code │ │  (AG2)  │
   └─────────┘ └───────┘ └───────┘ └──────┘ └─────────┘
```

Every framework connects via the same REST API. The only differences are how each framework defines "tools" — the HTTP calls are identical.
