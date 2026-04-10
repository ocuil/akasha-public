# Akasha + LangGraph — Shared Memory Multi-Agent Pipeline

> Four LangGraph agents share knowledge through Akasha's cognitive fabric — without custom wiring.

## Architecture

```
┌────────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Researcher │ →  │ Analyst  │ →  │  Writer  │ →  │  Critic  │
│ 🔍 facts   │    │ 📊 insight│    │ ✍️ report │    │ 🎯 review │
└─────┬──────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘
      │                │               │               │
      │    ┌───────────▼───────────────▼───────────────▼──┐
      └───→│              A K A S H A                      │
           │                                               │
           │  episodic/research/*/finding-*  ←── facts     │
           │  semantic/analysis/*/insights   ←── insights  │
           │  semantic/reports/*/latest      ←── report    │
           │  semantic/reviews/*/latest      ←── feedback  │
           └───────────────────────────────────────────────┘
```

**The key insight:** Agents don't pass data to each other directly. They write to Akasha and read from Akasha. This means:

- ✅ Any agent can be replaced without changing others
- ✅ New agents can join the pipeline by reading existing paths
- ✅ All knowledge persists across runs (semantic memory is permanent)
- ✅ Zero coordination code — pure read/write

## Quick Start

```bash
# 1. Start Akasha
docker run -d --name akasha -p 7777:7777 alejandrosl/akasha:latest

# 2. Install dependencies
pip install akasha-client langgraph

# 3. Run the pipeline
python langgraph_agents.py
```

## Expected Output

```
  🔍 researcher   Researching: AI Agent Infrastructure
  🔍 researcher     → AI Agent Infrastructure market grew 34% in 2025 (Gartner, conf: 92%)
  🔍 researcher     → Top 3 players control 60% of market (IDC, conf: 87%)
  🔍 researcher     → Enterprise adoption doubled YoY (McKinsey, conf: 95%)
  🔍 researcher     → Average ROI: 340% (Forrester, conf: 78%)
  🔍 researcher     ✓ 4 findings → episodic memory [12ms, 5 ops]

  📊 analyst       Analyzing findings: AI Agent Infrastructure
  📊 analyst         Found 4 research records in Akasha
  📊 analyst         → Key insight: strong growth trajectory with 88% avg confidence
  📊 analyst         ✓ Insights → semantic memory [4ms, 2 ops]

  ✍️ writer         Writing report: AI Agent Infrastructure
  ✍️ writer          → "Market Analysis: AI Agent Infrastructure" (4 facts, risk: low)
  ✍️ writer          ✓ Report → semantic memory [5ms, 3 ops]

  🎯 critic         Reviewing report: AI Agent Infrastructure
  🎯 critic          → ✅ Verdict: approved (100%)
  🎯 critic          ✓ Review → semantic memory [4ms, 3 ops]

  Pipeline complete:
    Total time:       28ms
    Akasha ops:       13
    Akasha API time:  25ms (89% of total)
    Overhead:         <1% in a real LLM pipeline
```

## How It Maps to Akasha's Memory Layers

| Layer | What's Stored | TTL | Purpose |
|-------|--------------|-----|---------|
| `memory/working/` | Agent status | 30 min | Coordination ("am I done?") |
| `memory/episodic/` | Research findings | 1 hour | Raw facts with timestamps |
| `memory/semantic/` | Insights + Reports | Permanent | Consolidated knowledge |

## Adding More Agents

Want to add a **Translator** that reads the report and outputs a Spanish version?

```python
def translator(state: PipelineState) -> PipelineState:
    report = akasha.get(f"memory/semantic/reports/{state['topic']}/latest")
    # ... translate ...
    akasha.put(f"memory/semantic/reports/{state['topic']}/latest-es", translated)
    return state

# Add to graph:
graph.add_node("translator", translator)
graph.add_edge("critic", "translator")
graph.add_edge("translator", END)
```

No changes to existing agents. The Translator reads from the same Akasha paths.

## Links

- [Akasha](https://github.com/ocuil/akasha-public) — The Shared Cognitive Fabric
- [Python SDK](https://pypi.org/project/akasha-client/) — `pip install akasha-client`
- [LangGraph](https://github.com/langchain-ai/langgraph) — Agent orchestration framework
