#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║          Akasha — Multi-Agent Stigmergy Pipeline Demo           ║
║                                                                  ║
║  Three agents coordinate through pheromone trails in Akasha's    ║
║  shared cognitive fabric — without ever talking to each other.   ║
║                                                                  ║
║  Scout → discovers data → deposits DISCOVERY pheromones          ║
║  Analyst → follows discoveries → deposits ANALYSIS pheromones    ║
║  Reporter → follows analyses → generates final report            ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import time
import json
import statistics
import threading
from datetime import datetime

from akasha_client import AkashaClient

# ── Configuration ─────────────────────────────────────────────────
AKASHA_URL = os.environ.get("AKASHA_URL", "https://localhost:7777")
AKASHA_USER = os.environ.get("AKASHA_USER", "akasha")
AKASHA_PASS = os.environ.get("AKASHA_PASS", "akasha")

# Simulated data sources
DATA_SOURCES = [
    {"id": "src-001", "type": "api", "name": "Weather Station Alpha", "records": 1_284},
    {"id": "src-002", "type": "csv", "name": "Sales Q1 Export", "records": 45_230},
    {"id": "src-003", "type": "api", "name": "IoT Sensor Grid B7", "records": 892_104},
    {"id": "src-004", "type": "db", "name": "Customer Feedback DB", "records": 12_891},
    {"id": "src-005", "type": "stream", "name": "Live Clickstream", "records": 3_400_000},
]

# ── Styling ───────────────────────────────────────────────────────
class C:
    SCOUT    = "\033[96m"   # Cyan
    ANALYST  = "\033[93m"   # Yellow
    REPORTER = "\033[92m"   # Green
    SYSTEM   = "\033[95m"   # Magenta
    METRIC   = "\033[97m"   # White bold
    DIM      = "\033[90m"   # Gray
    BOLD     = "\033[1m"
    RESET    = "\033[0m"
    OK       = "\033[92m✓\033[0m"
    WARN     = "\033[93m⚠\033[0m"
    FAIL     = "\033[91m✗\033[0m"


def log(agent: str, msg: str, color: str = C.DIM):
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    icon = {"scout": "🔍", "analyst": "📊", "reporter": "📝", "system": "⚙️"}.get(agent, "  ")
    padding = " " * (8 - len(agent))
    print(f"  {C.DIM}{ts}{C.RESET}  {icon} {color}{C.BOLD}{agent}{C.RESET}{padding} {color}{msg}{C.RESET}")


# ── Latency tracker ──────────────────────────────────────────────
latencies = {"write": [], "read": [], "pheromone": [], "query": []}
lock = threading.Lock()

def track(op: str, ms: float):
    with lock:
        latencies[op].append(ms)


# ══════════════════════════════════════════════════════════════════
#  AGENT 1: SCOUT — Discovers data sources
# ══════════════════════════════════════════════════════════════════
def agent_scout(client: AkashaClient):
    """
    The Scout agent discovers data sources and writes them to
    working memory. For each discovery, it deposits a pheromone
    on the 'discoveries' trail to signal other agents.
    """
    log("scout", "Agent started — scanning for data sources...", C.SCOUT)

    for source in DATA_SOURCES:
        # Write discovery to working memory
        path = f"memory/working/scout/discovery-{source['id']}"
        t0 = time.perf_counter()
        client.put(path, {
            "source_id": source["id"],
            "source_type": source["type"],
            "name": source["name"],
            "records_available": source["records"],
            "discovered_at": datetime.now().isoformat(),
            "status": "discovered",
        }, ttl_secs=3600)
        write_ms = (time.perf_counter() - t0) * 1000
        track("write", write_ms)

        # Deposit discovery pheromone — intensity proportional to data size
        intensity = min(1.0, source["records"] / 1_000_000)
        t0 = time.perf_counter()
        client.deposit_pheromone(
            trail=f"pipeline/discoveries/{source['id']}",
            signal_type="discovery",
            emitter="scout",
            intensity=max(0.3, intensity),
            half_life_secs=600,
            payload={"source_id": source["id"], "type": source["type"], "records": source["records"]},
        )
        pher_ms = (time.perf_counter() - t0) * 1000
        track("pheromone", pher_ms)

        log("scout", f"Discovered: {source['name']} ({source['records']:,} records) "
                      f"[write: {write_ms:.1f}ms, pheromone: {pher_ms:.1f}ms]", C.SCOUT)
        time.sleep(0.15)

    # Mark self as done
    client.put("memory/working/scout/status", {"state": "completed", "discoveries": len(DATA_SOURCES)})
    log("scout", f"Completed — {len(DATA_SOURCES)} sources discovered", C.SCOUT)


# ══════════════════════════════════════════════════════════════════
#  AGENT 2: ANALYST — Processes discovered data
# ══════════════════════════════════════════════════════════════════
def agent_analyst(client: AkashaClient):
    """
    The Analyst agent senses discovery pheromones, reads the discovered
    data, and writes analysis results to episodic memory.
    It follows the STRONGEST pheromone trails first (stigmergy!).
    """
    log("analyst", "Agent started — waiting for discovery pheromones...", C.ANALYST)
    time.sleep(1.0)  # Wait for Scout to deposit some pheromones

    # Sense discovery pheromones
    t0 = time.perf_counter()
    trails = client.sense_pheromones("pipeline/discoveries/*")
    sense_ms = (time.perf_counter() - t0) * 1000
    track("query", sense_ms)

    if not trails:
        log("analyst", "No discovery pheromones found — nothing to analyze", C.ANALYST)
        return

    log("analyst", f"Sensed {len(trails)} discovery pheromones [sense: {sense_ms:.1f}ms]", C.ANALYST)

    # Process each discovery (sorted by intensity — strongest first!)
    analyses_done = 0
    for trail in sorted(trails, key=lambda t: t.get("current_intensity", t.get("initial_intensity", 0)), reverse=True):
        # Extract source_id from the trail path: "pipeline/discoveries/src-XXX"
        trail_path = trail.get("trail", "")
        source_id = trail_path.split("/")[-1] if "/" in trail_path else trail_path
        intensity = trail.get("current_intensity", trail.get("initial_intensity", 0))

        # Read the discovery from working memory
        t0 = time.perf_counter()
        discovery, read_ms = client.timed_get(f"memory/working/scout/discovery-{source_id}")
        track("read", read_ms)

        if not discovery:
            continue

        source_data = discovery.get("value", discovery)
        records = source_data.get("records_available", 0)

        # Simulate analysis: compute a quality score
        quality_score = round(min(0.99, 0.5 + (records / 10_000_000) + (intensity * 0.3)), 2)

        # Write analysis result to episodic memory
        analysis = {
            "source_id": source_id,
            "source_name": source_data.get("name", source_id),
            "records_analyzed": records,
            "quality_score": quality_score,
            "pheromone_intensity": round(intensity, 3),
            "analysis_timestamp": datetime.now().isoformat(),
            "recommendation": "high-priority" if quality_score > 0.7 else "normal",
        }
        t0 = time.perf_counter()
        client.put(f"memory/episodic/pipeline/analysis-{source_id}", analysis)
        write_ms = (time.perf_counter() - t0) * 1000
        track("write", write_ms)

        # Deposit analysis pheromone
        t0 = time.perf_counter()
        client.deposit_pheromone(
            trail=f"pipeline/analyses/{source_id}",
            signal_type="success" if quality_score > 0.7 else "info",
            emitter="analyst",
            intensity=quality_score,
            half_life_secs=1200,
            payload={"source_id": source_id, "quality": quality_score, "recommendation": analysis["recommendation"]},
        )
        pher_ms = (time.perf_counter() - t0) * 1000
        track("pheromone", pher_ms)

        priority_flag = " ⭐" if quality_score > 0.7 else ""
        log("analyst", f"Analyzed: {source_data.get('name', source_id)} → quality={quality_score}{priority_flag} "
                        f"[read: {read_ms:.1f}ms, write: {write_ms:.1f}ms]", C.ANALYST)
        analyses_done += 1
        time.sleep(0.1)

    client.put("memory/working/analyst/status", {"state": "completed", "analyses": analyses_done})
    log("analyst", f"Completed — {analyses_done} sources analyzed", C.ANALYST)


# ══════════════════════════════════════════════════════════════════
#  AGENT 3: REPORTER — Generates final report
# ══════════════════════════════════════════════════════════════════
def agent_reporter(client: AkashaClient):
    """
    The Reporter agent waits for analysis pheromones, reads all
    analysis results from episodic memory, and writes a consolidated
    report to semantic memory (long-term knowledge).
    """
    log("reporter", "Agent started — waiting for analysis pheromones...", C.REPORTER)
    time.sleep(2.5)  # Wait for Analyst to finish

    # Sense analysis pheromones
    t0 = time.perf_counter()
    trails = client.sense_pheromones("pipeline/analyses/*")
    sense_ms = (time.perf_counter() - t0) * 1000
    track("query", sense_ms)

    if not trails:
        log("reporter", "No analysis pheromones found — nothing to report", C.REPORTER)
        return

    log("reporter", f"Sensed {len(trails)} analysis pheromones [sense: {sense_ms:.1f}ms]", C.REPORTER)

    # Read all analyses from episodic memory via glob query
    t0 = time.perf_counter()
    analyses_raw = client.query("memory/episodic/pipeline/*")
    query_ms = (time.perf_counter() - t0) * 1000
    track("query", query_ms)

    # Normalize: query returns [{path, value, ...}]
    analyses = []
    for record in analyses_raw:
        val = record.get("value", record) if isinstance(record, dict) else record
        if val:
            analyses.append(val)

    log("reporter", f"Retrieved {len(analyses)} analysis records [query: {query_ms:.1f}ms]", C.REPORTER)

    # Build consolidated report
    high_priority = []
    total_records = 0
    avg_quality = 0

    for value in analyses:
        src_id = value.get("source_id", "")
        quality = value.get("quality_score", 0)
        records = value.get("records_analyzed", 0)
        total_records += records
        avg_quality += quality
        if value.get("recommendation") == "high-priority":
            high_priority.append({"source_id": src_id, "quality": quality, "records": records})

    n = len(analyses) or 1
    avg_quality = round(avg_quality / n, 3)

    # Write report to semantic memory (long-term knowledge!)
    report = {
        "report_type": "pipeline-summary",
        "generated_at": datetime.now().isoformat(),
        "generated_by": "reporter",
        "total_sources_analyzed": len(analyses),
        "total_records_scanned": total_records,
        "average_quality_score": avg_quality,
        "high_priority_sources": high_priority,
        "recommendation": f"Focus on {len(high_priority)} high-priority sources ({total_records:,} total records)",
    }

    t0 = time.perf_counter()
    client.put("memory/semantic/pipeline/latest-report", report)
    write_ms = (time.perf_counter() - t0) * 1000
    track("write", write_ms)

    log("reporter", f"Report written to semantic memory [write: {write_ms:.1f}ms]", C.REPORTER)

    # Deposit completion pheromone
    client.deposit_pheromone(
        trail="pipeline/status",
        signal_type="success",
        emitter="reporter",
        intensity=1.0,
        half_life_secs=3600,
        payload={"status": "complete", "sources": len(analyses), "high_priority": len(high_priority)},
    )

    client.put("memory/working/reporter/status", {"state": "completed"})
    log("reporter", f"Completed — report covers {len(analyses)} sources, "
                     f"{len(high_priority)} high-priority, {total_records:,} records", C.REPORTER)

    return report


# ══════════════════════════════════════════════════════════════════
#  ORCHESTRATOR — Runs the pipeline and prints metrics
# ══════════════════════════════════════════════════════════════════
def print_banner():
    print(f"""
{C.BOLD}{C.SYSTEM}  ╔══════════════════════════════════════════════════════════════════╗
  ║          Akasha — Multi-Agent Stigmergy Pipeline Demo           ║
  ╚══════════════════════════════════════════════════════════════════╝{C.RESET}

  {C.DIM}Three agents coordinate through pheromone trails in Akasha's
  shared cognitive fabric — without ever talking to each other.{C.RESET}

  {C.SCOUT}🔍 Scout{C.RESET}    → discovers data sources     → deposits DISCOVERY pheromones
  {C.ANALYST}📊 Analyst{C.RESET}  → follows strongest trails   → deposits ANALYSIS pheromones
  {C.REPORTER}📝 Reporter{C.RESET} → reads analysis results      → writes report to semantic memory

  {C.DIM}Akasha URL: {AKASHA_URL}{C.RESET}
""")


def cleanup(client: AkashaClient):
    """Clean up demo data from previous runs."""
    patterns = [
        "memory/working/scout/*",
        "memory/working/analyst/*",
        "memory/working/reporter/*",
        "memory/episodic/pipeline/*",
        "memory/semantic/pipeline/*",
        "_pheromones/pipeline/*",
    ]
    for pattern in patterns:
        records = client.query(pattern)
        for r in records:
            path = r.get("path", "")
            if path:
                client.delete(path)


def print_metrics():
    """Print latency statistics."""
    print(f"""
{C.BOLD}{C.SYSTEM}  ┌──────────────────────────────────────────────────────────────────┐
  │                        PERFORMANCE METRICS                      │
  └──────────────────────────────────────────────────────────────────┘{C.RESET}
""")

    for op, values in latencies.items():
        if not values:
            continue
        p50 = statistics.median(values)
        p95 = sorted(values)[int(len(values) * 0.95)] if len(values) >= 2 else values[0]
        p99 = sorted(values)[int(len(values) * 0.99)] if len(values) >= 3 else values[-1]
        avg = statistics.mean(values)
        total = sum(values)

        # Color code based on latency
        color = C.REPORTER if p50 < 5 else (C.ANALYST if p50 < 20 else "\033[91m")

        print(f"  {C.METRIC}{C.BOLD}{op.upper():12s}{C.RESET}"
              f"  {color}P50: {p50:6.1f}ms{C.RESET}"
              f"  {color}P95: {p95:6.1f}ms{C.RESET}"
              f"  {color}P99: {p99:6.1f}ms{C.RESET}"
              f"  {C.DIM}avg: {avg:.1f}ms  ops: {len(values)}  total: {total:.0f}ms{C.RESET}")

    total_ops = sum(len(v) for v in latencies.values())
    total_time = sum(sum(v) for v in latencies.values())
    all_latencies = [v for vals in latencies.values() for v in vals]
    global_p50 = statistics.median(all_latencies) if all_latencies else 0

    print(f"""
  {C.DIM}─────────────────────────────────────────────────{C.RESET}
  {C.METRIC}{C.BOLD}Total operations:{C.RESET} {total_ops}
  {C.METRIC}{C.BOLD}Total API time:{C.RESET}   {total_time:.0f}ms
  {C.METRIC}{C.BOLD}Global P50:{C.RESET}       {global_p50:.1f}ms
  {C.METRIC}{C.BOLD}Throughput:{C.RESET}        {total_ops / (total_time / 1000):.0f} ops/sec (single-threaded, serial)
""")


def print_final_state(client: AkashaClient):
    """Print the final state of the cognitive fabric."""
    print(f"""
{C.BOLD}{C.SYSTEM}  ┌──────────────────────────────────────────────────────────────────┐
  │                     COGNITIVE FABRIC STATE                      │
  └──────────────────────────────────────────────────────────────────┘{C.RESET}
""")

    # Memory layers
    layers = client.memory_layers()
    if isinstance(layers, dict):
        for layer, count in layers.items():
            if isinstance(count, (int, float)):
                bar = "█" * min(30, int(count / 2))
                print(f"  {C.METRIC}{layer:12s}{C.RESET} {bar} {count}")
    print()

    # Active pheromones
    trails = client.sense_pheromones("pipeline/*")
    if trails:
        print(f"  {C.BOLD}Active pheromone trails:{C.RESET} {len(trails)}")
        for t in sorted(trails, key=lambda x: x.get("current_intensity", 0), reverse=True)[:8]:
            trail_name = t.get("trail", "?")
            intensity = t.get("current_intensity", t.get("initial_intensity", 0))
            signal = t.get("signal_type", "?")
            emitter = t.get("emitter", "?")
            bar = "▓" * max(1, int(intensity * 20))
            print(f"    {C.DIM}{trail_name:45s}{C.RESET} {bar} {intensity:.2f} ({signal} by {emitter})")
    print()

    # Final report
    report = client.get("memory/semantic/pipeline/latest-report")
    if report:
        val = report.get("value", report)
        print(f"  {C.BOLD}{C.REPORTER}Final Report (semantic memory):{C.RESET}")
        print(f"    Sources analyzed:      {val.get('total_sources_analyzed', '?')}")
        print(f"    Records scanned:       {val.get('total_records_scanned', 0):,}")
        print(f"    Avg quality score:     {val.get('average_quality_score', '?')}")
        hp = val.get("high_priority_sources", [])
        print(f"    High-priority sources: {len(hp)}")
        for src in hp:
            print(f"      ⭐ {src.get('source_id', '?')} — quality: {src.get('quality', 0)}, "
                  f"records: {src.get('records', 0):,}")
        print(f"    Recommendation:        {val.get('recommendation', '?')}")
    print()


def main():
    print_banner()

    # ── Connect to Akasha ─────────────────────────────────────────
    log("system", f"Connecting to {AKASHA_URL}...", C.SYSTEM)
    client = AkashaClient(AKASHA_URL)

    try:
        client.login(AKASHA_USER, AKASHA_PASS)
        log("system", f"Authenticated {C.OK}", C.SYSTEM)
    except Exception as e:
        log("system", f"Auth failed: {e} — trying without auth...", C.SYSTEM)

    health = client.health()
    log("system", f"Akasha v{health.get('version', '?')} — {health.get('records', 0)} records {C.OK}", C.SYSTEM)
    print()

    # ── Clean up previous run ────────────────────────────────────
    log("system", "Cleaning up previous demo data...", C.SYSTEM)
    cleanup(client)
    print()

    # ── Run pipeline ──────────────────────────────────────────────
    pipeline_start = time.perf_counter()

    print(f"  {C.BOLD}{C.SYSTEM}── Phase 1: Discovery ──────────────────────────────────────{C.RESET}\n")
    agent_scout(client)
    print()

    print(f"  {C.BOLD}{C.SYSTEM}── Phase 2: Analysis ───────────────────────────────────────{C.RESET}\n")
    agent_analyst(client)
    print()

    print(f"  {C.BOLD}{C.SYSTEM}── Phase 3: Reporting ──────────────────────────────────────{C.RESET}\n")
    agent_reporter(client)

    pipeline_elapsed = (time.perf_counter() - pipeline_start) * 1000
    print(f"\n  {C.BOLD}Pipeline completed in {pipeline_elapsed:.0f}ms{C.RESET}\n")

    # ── Metrics ───────────────────────────────────────────────────
    print_metrics()
    print_final_state(client)

    # ── Summary ───────────────────────────────────────────────────
    all_lats = [v for vals in latencies.values() for v in vals]
    p50 = statistics.median(all_lats) if all_lats else 0
    total_ops = len(all_lats)

    print(f"""  {C.BOLD}{C.SYSTEM}═══════════════════════════════════════════════════════════════{C.RESET}
  {C.BOLD}Key takeaways:{C.RESET}
    • {total_ops} memory operations completed in {pipeline_elapsed:.0f}ms
    • Median latency: {C.BOLD}{p50:.1f}ms{C.RESET} per operation
    • Zero LLM calls — pure data operations
    • Agents coordinated via pheromones (stigmergy) — no direct communication
    • Data flowed: Working → Episodic → Semantic memory (Nidra-ready)
  {C.BOLD}{C.SYSTEM}═══════════════════════════════════════════════════════════════{C.RESET}
""")


if __name__ == "__main__":
    main()
