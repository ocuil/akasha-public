#!/usr/bin/env python3
"""
📋 COORDINATOR AGENT — "The Manager"

Reads insights from semantic memory, monitors overall system health,
generates status reports in working memory, and deposits reinforcement
pheromones on important trails. Also reads procedural memory to
verify that runbooks exist for detected patterns.

Simulates: a project manager, an incident commander, a system health monitor.
"""

import random
import time
import uuid
from datetime import datetime, timezone

from akasha_client import AkashaClient

# ── Configuration ─────────────────────────────────────────────────
AKASHA_URL = "https://localhost:7777"
AGENT_NAME = "coordinator-agent"

DOMAINS = ["infrastructure", "security", "performance", "customer-feedback", "market-intel"]

STATUS_ACTIONS = [
    "Acknowledged incident in {domain} — assigning to on-call",
    "Escalating {domain} findings to engineering lead",
    "Scheduling review meeting for {domain} insights",
    "Creating Jira ticket for {type} pattern in {domain}",
    "Notifying stakeholders about {domain} trend",
    "Approving auto-remediation for {type} in {domain}",
    "Updating SLA dashboard with latest {domain} metrics",
    "Requesting budget for {domain} capacity expansion",
]


def coordinator_loop(client: AkashaClient):
    """Main coordinator loop — monitors, reports, coordinates."""
    cycle = 0

    while True:
        cycle += 1
        timestamp = datetime.now(timezone.utc).isoformat()
        report_id = str(uuid.uuid4())[:8]

        print(f"\n{'='*60}")
        print(f"📋 [{AGENT_NAME}] Cycle {cycle} — Monitoring system health...")

        # ── Phase 1: Read memory layer stats ─────────────────────
        time.sleep(random.uniform(1.5, 3.0))

        try:
            layers = client.memory_layers()
            print(f"   📊 Memory layers: {layers}")
        except Exception:
            print("   ⚠️ Could not read memory layers")
            layers = {}

        time.sleep(random.uniform(1.0, 2.0))

        # ── Phase 2: Scan all domains for insights ───────────────
        domain_health = {}
        for domain in DOMAINS:
            time.sleep(random.uniform(0.5, 1.5))  # Simula scan por dominio

            # Check episodic (recent events)
            episodes = client.query(f"memory/episodic/{domain}/*")
            ep_count = len(episodes) if isinstance(episodes, list) else 0

            # Check semantic (insights)
            insights = client.query(f"memory/semantic/{domain}/**")
            ins_count = len(insights) if isinstance(insights, list) else 0

            if ep_count > 0 or ins_count > 0:
                # Calculate health score
                severity_sum = 0.0
                for item in (insights if isinstance(insights, list) else []):
                    val = item.get("value", {})
                    if isinstance(val, dict):
                        severity_sum += val.get("severity_score", 0.0)

                health = max(0, 100 - int(severity_sum * 15) - ep_count * 3)
                domain_health[domain] = {
                    "episodes": ep_count,
                    "insights": ins_count,
                    "health_score": health,
                }
                status = "🟢" if health > 70 else "🟡" if health > 40 else "🔴"
                print(f"   {status} {domain}: health={health}, episodes={ep_count}, insights={ins_count}")

        time.sleep(random.uniform(1.0, 2.5))

        # ── Phase 3: Check pheromones for urgent signals ─────────
        print(f"   📡 Checking coordination signals...")
        trails = client.sense_pheromones()
        warnings = [t for t in trails if t.get("signal_type") == "warning"
                     and t.get("current_intensity", t.get("intensity", 0)) > 0.5]

        if warnings:
            print(f"   🚨 {len(warnings)} active warnings detected!")
            for w in warnings[:3]:
                payload = w.get("payload", {})
                trail = w.get("trail", "unknown")
                intensity = w.get("current_intensity", w.get("intensity", 0))
                print(f"      → {trail} (intensity={intensity:.2f})")

                # Reinforce important warnings
                if intensity > 0.6:
                    time.sleep(random.uniform(0.5, 1.0))
                    client.deposit_pheromone(
                        trail=trail,
                        signal_type="reinforcement",
                        emitter=AGENT_NAME,
                        intensity=min(1.0, intensity + 0.1),
                        half_life_secs=3600,
                        payload={"reinforced_by": AGENT_NAME, "original_intensity": intensity},
                    )
                    print(f"      ↑ Reinforced (new intensity={min(1.0, intensity + 0.1):.2f})")
        else:
            print(f"   ✅ No urgent warnings")

        time.sleep(random.uniform(1.0, 2.0))

        # ── Phase 4: Check procedural memory coverage ────────────
        print(f"   📖 Checking runbook coverage...")
        runbooks = client.query("memory/procedural/runbooks/*")
        rb_count = len(runbooks) if isinstance(runbooks, list) else 0
        runbook_types = set()
        for rb in (runbooks if isinstance(runbooks, list) else []):
            val = rb.get("value", {})
            if isinstance(val, dict):
                runbook_types.add(val.get("type", "unknown"))

        print(f"   📖 Runbooks available: {rb_count} types: {', '.join(runbook_types) if runbook_types else 'none'}")
        time.sleep(random.uniform(0.5, 1.5))

        # ── Phase 5: Generate status report (working memory) ─────
        worst_domain = None
        worst_health = 100
        for d, info in domain_health.items():
            if info["health_score"] < worst_health:
                worst_health = info["health_score"]
                worst_domain = d

        action = random.choice(STATUS_ACTIONS).format(
            domain=worst_domain or random.choice(DOMAINS),
            type=random.choice(list(runbook_types)) if runbook_types else "unknown",
        )

        report = {
            "report_id": report_id,
            "cycle": cycle,
            "timestamp": timestamp,
            "coordinator": AGENT_NAME,
            "domain_health": domain_health,
            "active_warnings": len(warnings),
            "runbook_coverage": rb_count,
            "overall_health": sum(d["health_score"] for d in domain_health.values()) // max(len(domain_health), 1) if domain_health else 100,
            "action_taken": action,
            "memory_layers": layers,
        }

        # Working memory — short TTL, this is a snapshot
        report_path = f"memory/working/coordinator/status/{report_id}"
        client.put(report_path, report, ttl_secs=120)  # 2 minutes TTL
        print(f"   📝 Status report: {report_path}")
        print(f"      Overall health: {report['overall_health']}%")
        print(f"      Action: {action}")

        # Also keep a rolling "latest" in semantic
        time.sleep(random.uniform(0.5, 1.0))
        client.put("memory/semantic/system/latest-status", {
            "timestamp": timestamp,
            "overall_health": report["overall_health"],
            "worst_domain": worst_domain,
            "worst_health": worst_health,
            "active_warnings": len(warnings),
            "action": action,
        })

        # ── Phase 6: Signal system status ────────────────────────
        overall = report["overall_health"]
        if overall < 50:
            client.deposit_pheromone(
                trail="system/health/critical",
                signal_type="warning",
                emitter=AGENT_NAME,
                intensity=0.95,
                half_life_secs=1800,
                payload={"health": overall, "worst_domain": worst_domain},
            )
            print(f"   🚨 CRITICAL: System health {overall}% — pheromone deposited")
        elif overall < 75:
            client.deposit_pheromone(
                trail="system/health/degraded",
                signal_type="warning",
                emitter=AGENT_NAME,
                intensity=0.6,
                half_life_secs=1200,
                payload={"health": overall, "worst_domain": worst_domain},
            )
            print(f"   ⚠️ DEGRADED: System health {overall}%")
        else:
            print(f"   🟢 System health: {overall}% — all clear")

        # ── Wait before next coordination cycle ──────────────────
        wait = random.uniform(15.0, 35.0)  # Coordinator cycles slower
        print(f"   ⏳ Next status check in {wait:.1f}s...")
        time.sleep(wait)


if __name__ == "__main__":
    print("📋 COORDINATOR AGENT starting...")
    print(f"   Connecting to {AKASHA_URL}")
    client = AkashaClient(AKASHA_URL)
    client.login()
    print("   ✅ Authenticated\n")
    coordinator_loop(client)
