#!/usr/bin/env python3
"""
🚀 SIMULACIÓN MULTI-AGENTE — Lanzador

Levanta los 3 agentes en procesos paralelos:
  🔍 Scout     — descubre incidentes/oportunidades (rápido, ~10s ciclo)
  🧠 Analyst   — analiza hallazgos, genera insights (medio, ~20s ciclo)
  📋 Coordinator — monitorea salud, genera reportes (lento, ~30s ciclo)

Los 3 agentes se coordinan exclusivamente a través de Akasha:
  - Scout escribe episodic + deposita pheromones
  - Analyst sensa pheromones, lee episodic, escribe semantic + procedural
  - Coordinator lee semantic, sensa pheromones, escribe working + semantic

Ctrl+C para detener todos los agentes.

Uso:
  python run_simulation.py                         # localhost:7777
  python run_simulation.py https://mi-server:7777  # server custom
"""

import sys
import subprocess
import signal
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

AGENTS = [
    {"name": "🔍 Scout", "script": "agent_scout.py", "color": "\033[33m"},       # Yellow
    {"name": "🧠 Analyst", "script": "agent_analyst.py", "color": "\033[36m"},    # Cyan
    {"name": "📋 Coordinator", "script": "agent_coordinator.py", "color": "\033[35m"},  # Magenta
]


def main():
    akasha_url = sys.argv[1] if len(sys.argv) > 1 else "https://localhost:7777"

    print("=" * 60)
    print("🚀 AKASHA MULTI-AGENT SIMULATION")
    print("=" * 60)
    print(f"   Server:  {akasha_url}")
    print(f"   Agents:  {len(AGENTS)}")
    print()
    for a in AGENTS:
        print(f"   {a['name']:20s} → {a['script']}")
    print()
    print("   Press Ctrl+C to stop all agents")
    print("=" * 60)
    print()

    # Set AKASHA_URL for all child processes
    env = os.environ.copy()
    env["AKASHA_URL"] = akasha_url

    processes = []
    for agent in AGENTS:
        script_path = os.path.join(SCRIPT_DIR, agent["script"])
        p = subprocess.Popen(
            [sys.executable, "-u", script_path],
            env=env,
            cwd=SCRIPT_DIR,
        )
        processes.append(p)
        print(f"   Started {agent['name']} (PID {p.pid})")

    print(f"\n   All {len(processes)} agents running. Watching for Ctrl+C...\n")

    # Wait for any process to exit or Ctrl+C
    def shutdown(signum, frame):
        print(f"\n\n{'='*60}")
        print("🛑 Shutting down all agents...")
        for p in processes:
            try:
                p.terminate()
            except Exception:
                pass
        for p in processes:
            try:
                p.wait(timeout=5)
            except Exception:
                p.kill()
        print("   All agents stopped.")
        print("=" * 60)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Wait forever until signal
    for p in processes:
        try:
            p.wait()
        except Exception:
            pass


if __name__ == "__main__":
    main()
