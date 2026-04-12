<div align="center">

# 🧠 Akasha MCP Server

**Give your AI agents persistent shared memory**

[![MCP](https://img.shields.io/badge/MCP-v1.0-blueviolet.svg)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-Apache--2.0-green.svg)](LICENSE)
[![Akasha](https://img.shields.io/badge/Akasha-v1.1.2-purple.svg)](https://github.com/ocuil/akasha-public)

*Your LLM forgets everything between conversations. Akasha fixes that.*

</div>

---

## The Problem

Every time you start a new conversation with Claude, Gemini, or GPT:
- ❌ It doesn't remember what it learned yesterday
- ❌ Multiple agents can't share knowledge
- ❌ There's no persistent memory between sessions
- ❌ You keep repeating the same context over and over

## The Solution

Akasha gives your AI a **persistent, shared memory** — like giving it a brain that doesn't reset.

```
Claude ──┐                    ┌── "What did we decide about the API?"
Gemini ──┼── Akasha Memory ──┤── "Agent-B is already working on that"
GPT ─────┘                    └── "Here's what we learned last week"
```

## What Can Your AI Do With Akasha?

| Tool | What it does | Example |
|------|-------------|---------|
| `akasha_write` | Save anything to persistent memory | *"Remember that the user prefers Python over JS"* |
| `akasha_read` | Recall saved memories | *"What do we know about the API design?"* |
| `akasha_query` | Search across all memories | *"Find everything related to deployment"* |
| `akasha_memory_store` | Write to cognitive layers (working/episodic/semantic/procedural) | *"Store this as a long-term fact"* |
| `akasha_memory_recall` | Recall from a specific layer | *"What procedures do we have for deployments?"* |
| `akasha_pheromone_emit` | Signal other agents (stigmergy) | *"Mark this task as in-progress"* |
| `akasha_pheromone_sense` | Sense what other agents are doing | *"Is anyone else working on the API?"* |
| `akasha_health` | Check system status | *"Is the memory system healthy?"* |
| `akasha_diagnostics` | Full cluster health assessment | *"Run a full diagnostic report"* |
| `akasha_agents` | List all connected agents | *"Who else is online?"* |

---

## Quick Setup (2 minutes)

### 1. Start Akasha

```bash
docker run -d --name akasha -p 7777:7777 -p 50051:50051 alejandrosl/akasha:latest
```

### 2. Get an API Key

```bash
# Login
TOKEN=$(curl -sk -X POST https://localhost:7777/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"akasha","password":"akasha"}' | jq -r .token)

# Create API key
curl -sk -X POST https://localhost:7777/api/v1/admin/keys \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"mcp-server","namespaces":["**"],"role":"agent"}' | jq .key
```

### 3. Connect to Your AI

<details>
<summary><b>Claude Desktop</b></summary>

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "akasha": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/ocuil/akasha-public#subdirectory=mcp-server", "akasha-mcp"],
      "env": {
        "AKASHA_URL": "https://localhost:7777",
        "AKASHA_API_KEY": "ak_your_key_here"
      }
    }
  }
}
```
</details>

<details>
<summary><b>Cursor</b></summary>

Add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "akasha": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/ocuil/akasha-public#subdirectory=mcp-server", "akasha-mcp"],
      "env": {
        "AKASHA_URL": "https://localhost:7777",
        "AKASHA_API_KEY": "ak_your_key_here"
      }
    }
  }
}
```
</details>

<details>
<summary><b>Manual (pip install)</b></summary>

```bash
pip install git+https://github.com/ocuil/akasha-public#subdirectory=mcp-server

# Run
AKASHA_URL=https://localhost:7777 \
AKASHA_API_KEY=ak_your_key_here \
akasha-mcp
```
</details>

---

## What Makes Akasha Different?

### 🐜 Stigmergy — Agents Coordinate Without Talking

Inspired by how ant colonies build complex structures without a blueprint:

```
Agent A writes: "task/enrichment → SUCCESS (quality: 0.95)"
Agent B reads:  "Someone already did enrichment with 95% quality — skip it"
Agent C reads:  "Two successes on enrichment — this is a reliable path"
```

No message queues, no APIs between agents. Just shared traces in the environment.

### 🧠 Four Layers of Memory

| Layer | Purpose | Lifespan |
|-------|---------|----------|
| **Working** | Current task scratchpad | Minutes |
| **Episodic** | What happened — events, outcomes | Hours → Days |
| **Semantic** | What we know — facts, patterns | Days → Permanent |
| **Procedural** | How to do things — workflows | Permanent |

### 🧘 Nidra — Automatic Memory Consolidation

Like human sleep, Akasha's background engine:
- Cleans up stale working memory
- Consolidates repeated patterns into long-term knowledge  
- Evaporates decayed signals automatically

---

## Resources & Prompts

### Resources (Read-Only Context)

| URI | Description |
|-----|-------------|
| `akasha://health` | Cluster health status |
| `akasha://memory/layers` | Memory layer distribution |
| `akasha://records/{path}` | Read any record by path |
| `akasha://agents/{agent_id}` | Agent state |
| `akasha://tree` | Full tree of all paths |
| `akasha://diagnostics` | Cluster diagnostic report |

### Prompt Templates

| Prompt | What it does |
|--------|-------------|
| `memory_consolidation` | Analyze and consolidate episodic memories into semantic knowledge |
| `agent_status_report` | Full system-wide agent & cluster status |
| `system_health_check` | Deep cluster health diagnostic |
| `knowledge_extraction` | Extract and organize knowledge on any topic |

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `AKASHA_URL` | `https://localhost:7777` | Akasha server endpoint |
| `AKASHA_API_KEY` | *(required)* | API key for authentication |
| `AKASHA_VERIFY_SSL` | `false` | Verify TLS certificates |

---

## Development

```bash
# Clone
git clone https://github.com/ocuil/akasha-public
cd akasha-public/mcp-server

# Install in dev mode
pip install -e .

# Interactive MCP inspector
fastmcp dev server.py

# Run with SSE transport
python server.py --transport sse --port 8765
```

---

## Learn More

- [Akasha Documentation](https://ocuil.github.io/akasha-public/)
- [API Reference](https://github.com/ocuil/akasha-public/blob/main/api-reference.md)
- [Python SDK](https://pypi.org/project/akasha-client/)
- [Node.js SDK](https://www.npmjs.com/package/akasha-memory)
- [Docker Hub](https://hub.docker.com/r/alejandrosl/akasha)

---

<div align="center">

**Built with [FastMCP](https://github.com/jlowin/fastmcp) · Powered by [Akasha](https://github.com/ocuil/akasha-public)**

*"Give your AI a memory that persists — across conversations, across agents, across time."*

</div>
