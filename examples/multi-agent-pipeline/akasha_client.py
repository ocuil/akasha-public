"""
Lightweight Akasha HTTP client for the demo.
Uses only `requests` — no SDK dependency required.
"""

import time
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class AkashaClient:
    """Minimal HTTP client for Akasha REST API."""

    def __init__(self, base_url: str = "https://localhost:7777", verify_ssl: bool = False):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.verify = verify_ssl
        self.session.headers.update({"Content-Type": "application/json"})
        self._token = None

    # ── Auth ──────────────────────────────────────────────────────
    def login(self, username: str = "akasha", password: str = "akasha") -> str:
        """Authenticate and store JWT token."""
        r = self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            json={"username": username, "password": password},
        )
        r.raise_for_status()
        self._token = r.json()["token"]
        self.session.headers["Authorization"] = f"Bearer {self._token}"
        return self._token

    # ── CRUD ──────────────────────────────────────────────────────
    def put(self, path: str, value: dict, ttl_secs: int | None = None) -> dict:
        """Write a record."""
        body = {"value": value}
        if ttl_secs:
            body["ttl_secs"] = ttl_secs
        r = self.session.post(f"{self.base_url}/api/v1/records/{path}", json=body)
        r.raise_for_status()
        return r.json()

    def get(self, path: str) -> dict | None:
        """Read a record. Returns None if not found."""
        r = self.session.get(f"{self.base_url}/api/v1/records/{path}")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    def delete(self, path: str) -> bool:
        """Delete a record."""
        r = self.session.delete(f"{self.base_url}/api/v1/records/{path}")
        return r.status_code in (200, 204)

    def query(self, pattern: str) -> list[dict]:
        """Glob query for records."""
        r = self.session.get(f"{self.base_url}/api/v1/query", params={"pattern": pattern})
        r.raise_for_status()
        data = r.json()
        return data if isinstance(data, list) else data.get("records", [])

    # ── Pheromones (Stigmergy) ────────────────────────────────────
    def deposit_pheromone(
        self,
        trail: str,
        signal_type: str,
        emitter: str,
        intensity: float = 1.0,
        half_life_secs: int = 300,
        payload: dict | None = None,
    ) -> dict:
        """Deposit a pheromone trace."""
        body = {
            "trail": trail,
            "signal_type": signal_type,
            "emitter": emitter,
            "intensity": intensity,
            "half_life_secs": half_life_secs,
        }
        if payload:
            body["payload"] = payload
        r = self.session.post(f"{self.base_url}/api/v1/pheromones", json=body)
        r.raise_for_status()
        return r.json()

    def sense_pheromones(self, pattern: str = "*") -> list[dict]:
        """Sense active pheromone trails."""
        r = self.session.get(f"{self.base_url}/api/v1/pheromones", params={"pattern": pattern})
        r.raise_for_status()
        data = r.json()
        return data if isinstance(data, list) else data.get("pheromones", data.get("trails", []))

    # ── Memory Layers ─────────────────────────────────────────────
    def memory_layers(self) -> dict:
        """Get memory layer record counts."""
        r = self.session.get(f"{self.base_url}/api/v1/memory/layers")
        r.raise_for_status()
        return r.json()

    # ── Health & Metrics ──────────────────────────────────────────
    def health(self) -> dict:
        r = self.session.get(f"{self.base_url}/api/v1/health")
        r.raise_for_status()
        return r.json()

    # ── Benchmarking helper ───────────────────────────────────────
    def timed_put(self, path: str, value: dict) -> float:
        """Write a record and return elapsed time in ms."""
        t0 = time.perf_counter()
        self.put(path, value)
        return (time.perf_counter() - t0) * 1000

    def timed_get(self, path: str) -> tuple[dict | None, float]:
        """Read a record and return (data, elapsed_ms)."""
        t0 = time.perf_counter()
        data = self.get(path)
        return data, (time.perf_counter() - t0) * 1000
