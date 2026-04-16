#!/usr/bin/env python3
"""
🧠 ANALYST AGENT — "The Thinker"

Senses discovery/warning pheromones, reads episodic findings,
"analyzes" them (simulated LLM thinking), and writes insights
to semantic memory. Also updates procedural memory with new
runbooks when patterns are detected.

Simulates: an AI analyst, a data scientist agent, a pattern detector.
"""

import random
import time
import uuid
from datetime import datetime, timezone
from collections import Counter

from akasha_client import AkashaClient

# ── Configuration ─────────────────────────────────────────────────
AKASHA_URL = "https://localhost:7777"
AGENT_NAME = "analyst-agent"

ANALYSIS_INSIGHTS = [
    "Correlation detected between {a} and {b} — likely shared root cause",
    "Frequency of {type} events increased 3x compared to baseline",
    "Service {svc} shows degradation pattern typical of memory leak (stage 2/4)",
    "Cost optimization: consolidating {a} and {b} could save ~$1,200/month",
    "User feedback cluster identified: {n} mentions of '{feature}' in 7 days",
    "Anomaly in {domain}: metrics deviate 2.3σ from 30-day average",
    "Risk assessment: {severity} findings in {domain} trending upward",
    "Capacity planning: {svc} will need scaling in ~2 weeks at current growth",
]

RUNBOOK_STEPS = {
    "cpu_spike": ["Check top processes", "Verify cron jobs", "Review recent deploys", "Scale horizontally if persistent"],
    "memory_leak": ["Capture heap dump", "Compare with baseline", "Check recent PR merges", "Restart as temporary fix"],
    "latency_increase": ["Check DB query times", "Review CDN cache hit rate", "Verify DNS resolution", "Check upstream dependencies"],
    "error_rate": ["Check error logs by type", "Verify downstream health", "Review circuit breaker state", "Rollback if recent deploy"],
    "cert_expiry": ["Generate new cert via Let's Encrypt", "Update K8s secret", "Verify cert chain", "Monitor renewal"],
    "anomaly_detected": ["Check WAF logs", "Cross-reference with threat intel", "Verify geo-IP origin", "Alert security team if persistent"],
}

SERVICES = ["auth-svc", "billing-svc", "notification-svc", "analytics-svc", "search-svc"]
FEATURES = ["bulk import", "SSO integration", "webhook retries", "PDF export", "dark mode"]


def analyst_loop(client: AkashaClient):
    """Main analyst loop — reads findings, produces insights."""
    cycle = 0

    while True:
        cycle += 1
        timestamp = datetime.now(timezone.utc).isoformat()

        print(f"\n{'='*60}")
        print(f"🧠 [{AGENT_NAME}] Cycle {cycle} — Sensing environment...")

        # ── Phase 1: Sense pheromones ────────────────────────────
        time.sleep(random.uniform(1.5, 3.0))  # Simula "despertar"

        trails = client.sense_pheromones()
        active = [t for t in trails if t.get("current_intensity", t.get("intensity", 0)) > 0.2]
        warnings = [t for t in active if t.get("signal_type") == "warning"]
        discoveries = [t for t in active if t.get("signal_type") == "discovery"]

        print(f"   📡 Active signals: {len(active)} ({len(warnings)} warnings, {len(discoveries)} discoveries)")

        if not active:
            wait = random.uniform(8.0, 15.0)
            print(f"   💤 No signals — sleeping {wait:.1f}s...")
            time.sleep(wait)
            continue

        time.sleep(random.uniform(1.0, 2.0))

        # ── Phase 2: Read episodic findings ──────────────────────
        # Pick a domain from the pheromone signals
        domains_seen = set()
        for t in active:
            payload = t.get("payload", {})
            if isinstance(payload, dict) and "domain" in payload:
                domains_seen.add(payload["domain"])

        if not domains_seen:
            domains_seen = {"infrastructure"}  # fallback

        target_domain = random.choice(list(domains_seen))
        print(f"   🔎 Analyzing domain: {target_domain}")
        time.sleep(random.uniform(1.0, 2.5))

        findings = client.query(f"memory/episodic/{target_domain}/*")
        finding_count = len(findings) if isinstance(findings, list) else 0
        print(f"   📋 Found {finding_count} episodic records in {target_domain}")
        time.sleep(random.uniform(1.5, 3.0))  # Simula "pensando"

        # ── Phase 3: Generate insight ────────────────────────────
        insight_id = str(uuid.uuid4())[:8]
        insight_template = random.choice(ANALYSIS_INSIGHTS)

        # Fill placeholders
        types_seen = []
        for f in (findings if isinstance(findings, list) else []):
            val = f.get("value", {})
            if isinstance(val, dict):
                types_seen.append(val.get("type", "unknown"))

        type_counts = Counter(types_seen)
        most_common_type = type_counts.most_common(1)[0][0] if type_counts else "unknown"

        insight_text = insight_template.format(
            a=random.choice(SERVICES),
            b=random.choice(SERVICES),
            type=most_common_type,
            svc=random.choice(SERVICES),
            n=random.randint(3, 12),
            feature=random.choice(FEATURES),
            domain=target_domain,
            severity=random.choice(["warning", "critical"]),
        )

        severity_score = random.uniform(0.3, 0.95)
        confidence = random.uniform(0.6, 0.98)

        insight = {
            "id": insight_id,
            "domain": target_domain,
            "insight": insight_text,
            "severity_score": round(severity_score, 2),
            "confidence": round(confidence, 2),
            "based_on_findings": finding_count,
            "most_common_type": most_common_type,
            "analyst": AGENT_NAME,
            "analyzed_at": timestamp,
        }

        print(f"   💡 Insight: {insight_text}")
        print(f"      Confidence: {confidence:.0%} | Severity: {severity_score:.0%}")
        time.sleep(random.uniform(0.5, 1.5))

        # ── Phase 4: Write to semantic memory ────────────────────
        semantic_path = f"memory/semantic/{target_domain}/insights/{insight_id}"
        client.put(semantic_path, insight)
        print(f"   💾 Saved insight to: {semantic_path}")
        time.sleep(random.uniform(0.5, 1.0))

        # ── Phase 5: Update procedural runbook if pattern found ──
        if most_common_type in RUNBOOK_STEPS and random.random() > 0.5:
            runbook_path = f"memory/procedural/runbooks/{most_common_type}"
            existing_runbook = client.get(runbook_path)

            steps = RUNBOOK_STEPS[most_common_type]
            if existing_runbook:
                print(f"   📖 Runbook for '{most_common_type}' exists — reinforcing")
                runbook_data = existing_runbook.get("value", {})
                runbook_data["times_validated"] = runbook_data.get("times_validated", 0) + 1
                runbook_data["last_validated"] = timestamp
            else:
                print(f"   📝 Creating new runbook for '{most_common_type}'")
                runbook_data = {
                    "type": most_common_type,
                    "steps": steps,
                    "created_by": AGENT_NAME,
                    "created_at": timestamp,
                    "times_validated": 1,
                    "last_validated": timestamp,
                }

            client.put(runbook_path, runbook_data)
            print(f"   💾 Procedural memory updated: {runbook_path}")
            time.sleep(random.uniform(0.5, 1.0))

        # ── Phase 6: Signal if high severity ─────────────────────
        if severity_score > 0.7:
            client.deposit_pheromone(
                trail=f"insights/{target_domain}/{insight_id}",
                signal_type="warning" if severity_score > 0.85 else "discovery",
                emitter=AGENT_NAME,
                intensity=severity_score,
                half_life_secs=2400,
                payload={"insight_id": insight_id, "domain": target_domain, "severity": round(severity_score, 2)},
            )
            signal_type = "⚠️ WARNING" if severity_score > 0.85 else "💡 DISCOVERY"
            print(f"   🧪 Pheromone: {signal_type} (intensity={severity_score:.2f})")

        # ── Wait before next analysis cycle ──────────────────────
        wait = random.uniform(10.0, 25.0)  # Analyst thinks slower
        print(f"   ⏳ Next analysis in {wait:.1f}s...")
        time.sleep(wait)


if __name__ == "__main__":
    print("🧠 ANALYST AGENT starting...")
    print(f"   Connecting to {AKASHA_URL}")
    client = AkashaClient(AKASHA_URL)
    client.login()
    print("   ✅ Authenticated\n")
    analyst_loop(client)
