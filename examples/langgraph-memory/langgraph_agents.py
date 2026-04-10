#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║     Akasha + LangGraph — Shared Memory Multi-Agent Pipeline      ║
║                                                                  ║
║  Four LangGraph agents share knowledge through Akasha's          ║
║  cognitive fabric. No custom wiring — agents read/write to       ║
║  shared memory and coordinate via pheromone trails.               ║
║                                                                  ║
║  Researcher → finds information → writes to episodic memory      ║
║  Analyst    → reads findings    → writes insights to semantic    ║
║  Writer     → reads insights    → produces final document       ║
║  Critic     → reviews document  → writes feedback               ║
╚══════════════════════════════════════════════════════════════════╝

Requirements:
    pip install akasha-client langgraph

Usage:
    # Start Akasha first:
    docker run -d -p 7777:7777 alejandrosl/akasha:latest

    # Run:
    python langgraph_agents.py
"""

import time
import json
from datetime import datetime
from typing import TypedDict, Annotated

from langgraph.graph import StateGraph, END

from akasha import AkashaHttpClient

# ── Akasha connection ───────────────────────────────────────────
akasha = AkashaHttpClient("https://localhost:7777", verify_ssl=False)

# ── Colors for terminal output ──────────────────────────────────
class C:
    RESEARCH = "\033[96m"    # Cyan
    ANALYST  = "\033[93m"    # Yellow
    WRITER   = "\033[92m"    # Green
    CRITIC   = "\033[95m"    # Magenta
    SYSTEM   = "\033[90m"
    BOLD     = "\033[1m"
    RESET    = "\033[0m"

def log(agent: str, msg: str, color: str):
    ts = datetime.now().strftime("%H:%M:%S")
    icons = {"researcher": "🔍", "analyst": "📊", "writer": "✍️", "critic": "🎯"}
    print(f"  {C.SYSTEM}{ts}{C.RESET}  {icons.get(agent, '  ')} {color}{C.BOLD}{agent:12s}{C.RESET} {color}{msg}{C.RESET}")


# ── LangGraph State ─────────────────────────────────────────────
class PipelineState(TypedDict):
    topic: str
    phase: str
    akasha_ops: int
    total_ms: float


# ══════════════════════════════════════════════════════════════════
#  NODE 1: RESEARCHER
# ══════════════════════════════════════════════════════════════════
def researcher(state: PipelineState) -> PipelineState:
    topic = state["topic"]
    log("researcher", f"Researching: {topic}", C.RESEARCH)

    # Simulate research findings
    findings = [
        {"fact": f"{topic} market grew 34% in 2025", "confidence": 0.92, "source": "Gartner"},
        {"fact": f"Top 3 players control 60% of {topic} market", "confidence": 0.87, "source": "IDC"},
        {"fact": f"Enterprise adoption of {topic} doubled YoY", "confidence": 0.95, "source": "McKinsey"},
        {"fact": f"Average ROI for {topic} implementations: 340%", "confidence": 0.78, "source": "Forrester"},
    ]

    t0 = time.perf_counter()
    ops = 0

    # Write each finding to Akasha episodic memory
    for i, finding in enumerate(findings):
        akasha.put(
            f"memory/episodic/research/{topic}/finding-{i}",
            {**finding, "discovered_at": datetime.now().isoformat(), "researcher": "agent-researcher"},
            ttl_seconds=3600,  # 1 hour retention
        )
        ops += 1
        log("researcher", f"  → {finding['fact']} ({finding['source']}, conf: {finding['confidence']})", C.RESEARCH)

    # Mark research complete
    akasha.put(f"memory/working/researcher/status", {
        "topic": topic, "state": "complete", "findings": len(findings)
    })
    ops += 1

    elapsed = (time.perf_counter() - t0) * 1000
    log("researcher", f"  ✓ {len(findings)} findings → episodic memory [{elapsed:.0f}ms, {ops} ops]", C.RESEARCH)

    return {**state, "phase": "research_complete", "akasha_ops": state["akasha_ops"] + ops, "total_ms": state["total_ms"] + elapsed}


# ══════════════════════════════════════════════════════════════════
#  NODE 2: ANALYST
# ══════════════════════════════════════════════════════════════════
def analyst(state: PipelineState) -> PipelineState:
    topic = state["topic"]
    log("analyst", f"Analyzing findings for: {topic}", C.ANALYST)

    t0 = time.perf_counter()
    ops = 0

    # Read all research findings from Akasha
    findings = akasha.query(f"memory/episodic/research/{topic}/*")
    ops += 1

    log("analyst", f"  Found {len(findings)} research records in Akasha", C.ANALYST)

    # Analyze: compute aggregate insights
    confidences = [r.value.get("confidence", 0) for r in findings if r.value]
    sources = list(set(r.value.get("source", "") for r in findings if r.value))
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0

    insights = {
        "topic": topic,
        "total_findings": len(findings),
        "average_confidence": round(avg_confidence, 3),
        "sources_consulted": sources,
        "key_insight": f"{topic} shows strong growth trajectory with {avg_confidence:.0%} average confidence across {len(sources)} sources",
        "risk_level": "low" if avg_confidence > 0.85 else "medium",
        "analyzed_at": datetime.now().isoformat(),
    }

    # Write insights to semantic memory (permanent knowledge)
    akasha.put(f"memory/semantic/analysis/{topic}/insights", insights)
    ops += 1

    elapsed = (time.perf_counter() - t0) * 1000
    log("analyst", f"  → Key insight: {insights['key_insight']}", C.ANALYST)
    log("analyst", f"  ✓ Insights → semantic memory [{elapsed:.0f}ms, {ops} ops]", C.ANALYST)

    return {**state, "phase": "analysis_complete", "akasha_ops": state["akasha_ops"] + ops, "total_ms": state["total_ms"] + elapsed}


# ══════════════════════════════════════════════════════════════════
#  NODE 3: WRITER
# ══════════════════════════════════════════════════════════════════
def writer(state: PipelineState) -> PipelineState:
    topic = state["topic"]
    log("writer", f"Writing report for: {topic}", C.WRITER)

    t0 = time.perf_counter()
    ops = 0

    # Read insights from Akasha semantic memory
    insights_record = akasha.get(f"memory/semantic/analysis/{topic}/insights")
    ops += 1

    if not insights_record:
        log("writer", "  ⚠ No insights found — skipping", C.WRITER)
        return {**state, "phase": "write_skipped"}

    insights = insights_record.value

    # Read original findings for detail
    findings = akasha.query(f"memory/episodic/research/{topic}/*")
    ops += 1

    # Generate report
    facts_list = "\n".join(
        f"  • {r.value.get('fact', '?')} (Source: {r.value.get('source', '?')}, Confidence: {r.value.get('confidence', 0):.0%})"
        for r in findings if r.value
    )

    report = {
        "title": f"Market Analysis: {topic}",
        "executive_summary": insights.get("key_insight", ""),
        "risk_assessment": insights.get("risk_level", "unknown"),
        "detailed_findings": facts_list,
        "sources": insights.get("sources_consulted", []),
        "methodology": "Multi-agent pipeline via Akasha shared cognitive fabric",
        "generated_at": datetime.now().isoformat(),
        "version": 1,
    }

    # Write report to semantic memory
    akasha.put(f"memory/semantic/reports/{topic}/latest", report)
    ops += 1

    elapsed = (time.perf_counter() - t0) * 1000
    log("writer", f"  → \"{report['title']}\" ({len(findings)} facts, risk: {report['risk_assessment']})", C.WRITER)
    log("writer", f"  ✓ Report → semantic memory [{elapsed:.0f}ms, {ops} ops]", C.WRITER)

    return {**state, "phase": "write_complete", "akasha_ops": state["akasha_ops"] + ops, "total_ms": state["total_ms"] + elapsed}


# ══════════════════════════════════════════════════════════════════
#  NODE 4: CRITIC
# ══════════════════════════════════════════════════════════════════
def critic(state: PipelineState) -> PipelineState:
    topic = state["topic"]
    log("critic", f"Reviewing report for: {topic}", C.CRITIC)

    t0 = time.perf_counter()
    ops = 0

    # Read the report from Akasha
    report_record = akasha.get(f"memory/semantic/reports/{topic}/latest")
    ops += 1

    if not report_record:
        log("critic", "  ⚠ No report found — skipping", C.CRITIC)
        return {**state, "phase": "review_skipped"}

    report = report_record.value

    # Read the original insights for cross-validation
    insights_record = akasha.get(f"memory/semantic/analysis/{topic}/insights")
    ops += 1

    # Evaluate
    has_summary = bool(report.get("executive_summary"))
    has_sources = len(report.get("sources", [])) > 0
    has_findings = bool(report.get("detailed_findings"))
    confidence = insights_record.value.get("average_confidence", 0) if insights_record else 0

    score = sum([has_summary, has_sources, has_findings, confidence > 0.8]) / 4
    verdict = "approved" if score >= 0.75 else "needs_revision"

    feedback = {
        "report_path": f"memory/semantic/reports/{topic}/latest",
        "quality_score": round(score, 2),
        "verdict": verdict,
        "checks": {
            "has_executive_summary": has_summary,
            "has_cited_sources": has_sources,
            "has_detailed_findings": has_findings,
            "high_confidence_data": confidence > 0.8,
        },
        "reviewer": "agent-critic",
        "reviewed_at": datetime.now().isoformat(),
    }

    # Write feedback to Akasha
    akasha.put(f"memory/semantic/reviews/{topic}/latest", feedback)
    ops += 1

    elapsed = (time.perf_counter() - t0) * 1000
    emoji = "✅" if verdict == "approved" else "🔄"
    log("critic", f"  → {emoji} Verdict: {verdict} (score: {score:.0%})", C.CRITIC)
    log("critic", f"  ✓ Review → semantic memory [{elapsed:.0f}ms, {ops} ops]", C.CRITIC)

    return {**state, "phase": "review_complete", "akasha_ops": state["akasha_ops"] + ops, "total_ms": state["total_ms"] + elapsed}


# ══════════════════════════════════════════════════════════════════
#  BUILD LANGGRAPH
# ══════════════════════════════════════════════════════════════════
def build_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("researcher", researcher)
    graph.add_node("analyst", analyst)
    graph.add_node("writer", writer)
    graph.add_node("critic", critic)

    graph.set_entry_point("researcher")
    graph.add_edge("researcher", "analyst")
    graph.add_edge("analyst", "writer")
    graph.add_edge("writer", "critic")
    graph.add_edge("critic", END)

    return graph.compile()


# ══════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════
def main():
    print(f"""
{C.BOLD}{C.SYSTEM}  ╔══════════════════════════════════════════════════════════════════╗
  ║     Akasha + LangGraph — Shared Memory Multi-Agent Pipeline      ║
  ╚══════════════════════════════════════════════════════════════════╝{C.RESET}

  {C.SYSTEM}Four agents share knowledge through Akasha's cognitive fabric.
  No custom wiring — agents read/write to shared memory.{C.RESET}

  {C.RESEARCH}🔍 Researcher{C.RESET}  → discovers facts     → episodic memory
  {C.ANALYST}📊 Analyst{C.RESET}     → synthesizes insights → semantic memory
  {C.WRITER}✍️  Writer{C.RESET}      → produces report      → semantic memory
  {C.CRITIC}🎯 Critic{C.RESET}      → reviews & scores     → semantic memory
""")

    # Verify Akasha is running
    try:
        health = akasha.health()
        log("system", f"Akasha v{health.get('version', '?')} — {health.get('records', 0)} records ✓", C.SYSTEM)
    except Exception as e:
        print(f"\n  ❌ Cannot connect to Akasha at https://localhost:7777")
        print(f"     Start it first: docker run -d -p 7777:7777 alejandrosl/akasha:latest\n")
        return

    # Run the LangGraph pipeline
    topic = "AI Agent Infrastructure"
    print(f"\n  {C.BOLD}Topic: \"{topic}\"{C.RESET}\n")

    graph = build_graph()
    pipeline_start = time.perf_counter()

    result = graph.invoke({
        "topic": topic,
        "phase": "started",
        "akasha_ops": 0,
        "total_ms": 0.0,
    })

    pipeline_ms = (time.perf_counter() - pipeline_start) * 1000

    # Print summary
    print(f"""
{C.BOLD}{C.SYSTEM}  ══════════════════════════════════════════════════════════════════{C.RESET}

  {C.BOLD}Pipeline complete:{C.RESET}
    Total time:       {pipeline_ms:.0f}ms
    Akasha ops:       {result['akasha_ops']}
    Akasha API time:  {result['total_ms']:.0f}ms ({result['total_ms']/pipeline_ms*100:.1f}% of total)
    Overhead:         {C.BOLD}{result['total_ms']/pipeline_ms*100:.1f}%{C.RESET} — the rest is pure application logic

  {C.BOLD}Memory state after pipeline:{C.RESET}""")

    # Show what's in Akasha now
    for layer in ["episodic", "semantic"]:
        records = akasha.query(f"memory/{layer}/**")
        paths = [r.path for r in records]
        print(f"    {layer:12s} → {len(paths)} records")
        for p in paths[:5]:
            print(f"                   {C.SYSTEM}{p}{C.RESET}")

    # Show the final report
    report = akasha.get(f"memory/semantic/reports/{topic}/latest")
    review = akasha.get(f"memory/semantic/reviews/{topic}/latest")
    if report and review:
        print(f"""
  {C.BOLD}Final report:{C.RESET}    "{report.value.get('title', '?')}"
  {C.BOLD}Risk assessment:{C.RESET} {report.value.get('risk_assessment', '?')}
  {C.BOLD}Critic verdict:{C.RESET}  {review.value.get('verdict', '?')} ({review.value.get('quality_score', 0):.0%})
""")

    print(f"""  {C.BOLD}{C.SYSTEM}══════════════════════════════════════════════════════════════════{C.RESET}
  {C.BOLD}Key takeaway:{C.RESET}
    Akasha consumed only {C.BOLD}{result['total_ms']:.0f}ms{C.RESET} for {result['akasha_ops']} memory operations.
    Agents shared knowledge without custom pipelines or message queues.
    Data flowed naturally: episodic → semantic → reports → reviews.
  {C.BOLD}{C.SYSTEM}══════════════════════════════════════════════════════════════════{C.RESET}
""")


if __name__ == "__main__":
    main()
