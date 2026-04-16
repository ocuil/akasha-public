#!/usr/bin/env python3
"""
🔍 SCOUT AGENT — "The Explorer"

Continuously discovers new "incidents" and "opportunities" in the wild.
Writes findings to episodic memory and deposits discovery pheromones
so other agents know there's work to do.

Simulates: a monitoring agent, a web scraper, a ticket intake system.
"""

import random
import time
import uuid
from datetime import datetime, timezone

from akasha_client import AkashaClient

# ── Configuration ─────────────────────────────────────────────────
AKASHA_URL = "https://localhost:7777"
AGENT_NAME = "scout-agent"

# Simulated domains the scout patrols
DOMAINS = ["infrastructure", "security", "performance", "customer-feedback", "market-intel"]

INCIDENT_TEMPLATES = [
    {"type": "cpu_spike", "severity": "warning", "desc": "CPU usage above 85% on node {node}"},
    {"type": "memory_leak", "severity": "critical", "desc": "Memory growing at 2MB/min in service {svc}"},
    {"type": "latency_increase", "severity": "warning", "desc": "P99 latency up 40% in {region} region"},
    {"type": "disk_space", "severity": "info", "desc": "Disk at 72% on volume {vol}"},
    {"type": "cert_expiry", "severity": "warning", "desc": "TLS cert for {domain} expires in 14 days"},
    {"type": "error_rate", "severity": "critical", "desc": "Error rate 5.2% in {svc} (threshold: 1%)"},
    {"type": "dependency_update", "severity": "info", "desc": "New version of {lib} available (security fix)"},
    {"type": "anomaly_detected", "severity": "warning", "desc": "Unusual traffic pattern from {ip_range}"},
]

OPPORTUNITY_TEMPLATES = [
    {"type": "cost_saving", "desc": "Unused EC2 instances in {region}: potential $2,400/mo saving"},
    {"type": "scaling_hint", "desc": "Service {svc} consistently under 20% load — candidate for downscale"},
    {"type": "user_feedback", "desc": "5 users requested feature '{feature}' this week"},
    {"type": "competitor_move", "desc": "Competitor X launched {feature} — market gap identified"},
]

NODES = ["akasha-01", "akasha-02", "akasha-03", "web-01", "api-gateway"]
SERVICES = ["auth-svc", "billing-svc", "notification-svc", "analytics-svc", "search-svc"]
REGIONS = ["us-east-1", "eu-west-1", "ap-southeast-1"]
FEATURES = ["bulk import", "SSO integration", "webhook retries", "PDF export", "dark mode"]


def random_fill(template: dict) -> dict:
    """Fill template placeholders with random values."""
    result = dict(template)
    desc = result["desc"]
    desc = desc.replace("{node}", random.choice(NODES))
    desc = desc.replace("{svc}", random.choice(SERVICES))
    desc = desc.replace("{region}", random.choice(REGIONS))
    desc = desc.replace("{vol}", f"/dev/xvd{random.choice('abcdef')}")
    desc = desc.replace("{domain}", f"{random.choice(['api','app','cdn'])}.acme.io")
    desc = desc.replace("{lib}", random.choice(["openssl", "tokio", "reqwest", "serde"]))
    desc = desc.replace("{ip_range}", f"203.0.{random.randint(1,254)}.0/24")
    desc = desc.replace("{feature}", random.choice(FEATURES))
    result["desc"] = desc
    return result


def scout_loop(client: AkashaClient):
    """Main scout loop — discovers incidents and opportunities."""
    cycle = 0

    while True:
        cycle += 1
        domain = random.choice(DOMAINS)
        finding_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now(timezone.utc).isoformat()

        # ── Phase 1: Check existing knowledge ────────────────────
        print(f"\n{'='*60}")
        print(f"🔍 [{AGENT_NAME}] Cycle {cycle} — Patrolling domain: {domain}")
        time.sleep(random.uniform(1.0, 2.5))  # Simula escaneo

        existing = client.query(f"memory/semantic/{domain}/*")
        known_count = len(existing) if isinstance(existing, list) else 0
        print(f"   📚 Known facts in {domain}: {known_count}")
        time.sleep(random.uniform(0.5, 1.5))

        # ── Phase 2: Discover something ──────────────────────────
        is_incident = random.random() > 0.35  # 65% incidents, 35% opportunities

        if is_incident:
            template = random_fill(random.choice(INCIDENT_TEMPLATES))
            finding = {
                "id": finding_id,
                "category": "incident",
                "domain": domain,
                "type": template["type"],
                "severity": template["severity"],
                "description": template["desc"],
                "discovered_by": AGENT_NAME,
                "discovered_at": timestamp,
                "status": "new",
            }
            emoji = "🚨" if template["severity"] == "critical" else "⚠️"
            print(f"   {emoji} Incident discovered: {template['desc']}")
        else:
            template = random_fill(random.choice(OPPORTUNITY_TEMPLATES))
            finding = {
                "id": finding_id,
                "category": "opportunity",
                "domain": domain,
                "type": template["type"],
                "description": template["desc"],
                "discovered_by": AGENT_NAME,
                "discovered_at": timestamp,
                "potential_impact": random.choice(["low", "medium", "high"]),
            }
            print(f"   💡 Opportunity found: {template['desc']}")

        time.sleep(random.uniform(1.0, 3.0))  # Simula análisis

        # ── Phase 3: Write to episodic memory ────────────────────
        path = f"memory/episodic/{domain}/{finding_id}"
        client.put(path, finding, ttl_secs=3600)
        print(f"   💾 Saved to: {path}")
        time.sleep(random.uniform(0.3, 0.8))

        # ── Phase 4: Deposit pheromone ───────────────────────────
        if is_incident:
            severity = finding["severity"]
            intensity = {"info": 0.3, "warning": 0.7, "critical": 0.95}[severity]
            signal = "warning" if severity in ("warning", "critical") else "discovery"
        else:
            intensity = {"low": 0.3, "medium": 0.5, "high": 0.8}[finding["potential_impact"]]
            signal = "discovery"

        client.deposit_pheromone(
            trail=f"findings/{domain}/{finding_id}",
            signal_type=signal,
            emitter=AGENT_NAME,
            intensity=intensity,
            half_life_secs=1800,
            payload={"finding_id": finding_id, "domain": domain, "type": finding.get("type")},
        )
        print(f"   🧪 Pheromone deposited: {signal} (intensity={intensity:.1f}) on findings/{domain}")

        # ── Phase 5: Update domain knowledge count ───────────────
        time.sleep(random.uniform(0.5, 1.0))
        stats_path = f"memory/semantic/{domain}/scan-stats"
        stats = client.get(stats_path)
        current_stats = stats.get("value", {}) if stats else {}
        current_stats["total_scans"] = current_stats.get("total_scans", 0) + 1
        current_stats["last_scan"] = timestamp
        current_stats["last_finding_type"] = finding.get("type", "unknown")
        client.put(stats_path, current_stats)
        print(f"   📊 Updated scan stats (total: {current_stats['total_scans']})")

        # ── Wait before next patrol ──────────────────────────────
        wait = random.uniform(5.0, 15.0)  # 5-15 seconds between discoveries
        print(f"   ⏳ Next patrol in {wait:.1f}s...")
        time.sleep(wait)


if __name__ == "__main__":
    print("🔍 SCOUT AGENT starting...")
    print(f"   Connecting to {AKASHA_URL}")
    client = AkashaClient(AKASHA_URL)
    client.login()
    print("   ✅ Authenticated\n")
    scout_loop(client)
