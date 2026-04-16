"""
Lightweight Akasha HTTP client for simulations.
"""

import time
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class AkashaClient:
    def __init__(self, base_url: str = "https://localhost:7777", verify_ssl: bool = False):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.verify = verify_ssl
        self.session.headers.update({"Content-Type": "application/json"})

    def login(self, username: str = "akasha", password: str = "akasha") -> str:
        r = self.session.post(f"{self.base_url}/api/v1/auth/login", json={"username": username, "password": password})
        r.raise_for_status()
        token = r.json()["token"]
        self.session.headers["Authorization"] = f"Bearer {token}"
        return token

    def put(self, path: str, value: dict, ttl_secs: int | None = None) -> dict:
        body = {"value": value}
        if ttl_secs:
            body["ttl_secs"] = ttl_secs
        r = self.session.post(f"{self.base_url}/api/v1/records/{path}", json=body)
        r.raise_for_status()
        return r.json()

    def get(self, path: str) -> dict | None:
        r = self.session.get(f"{self.base_url}/api/v1/records/{path}")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    def query(self, pattern: str) -> list[dict]:
        r = self.session.get(f"{self.base_url}/api/v1/query", params={"pattern": pattern})
        r.raise_for_status()
        data = r.json()
        return data if isinstance(data, list) else data.get("records", [])

    def deposit_pheromone(self, trail: str, signal_type: str, emitter: str,
                          intensity: float = 1.0, half_life_secs: int = 300,
                          payload: dict | None = None) -> dict:
        body = {"trail": trail, "signal_type": signal_type, "emitter": emitter,
                "intensity": intensity, "half_life_secs": half_life_secs}
        if payload:
            body["payload"] = payload
        r = self.session.post(f"{self.base_url}/api/v1/pheromones", json=body)
        r.raise_for_status()
        return r.json()

    def sense_pheromones(self) -> list[dict]:
        r = self.session.get(f"{self.base_url}/api/v1/pheromones")
        r.raise_for_status()
        data = r.json()
        return data if isinstance(data, list) else data.get("pheromones", data.get("trails", []))

    def memory_layers(self) -> dict:
        r = self.session.get(f"{self.base_url}/api/v1/memory/layers")
        r.raise_for_status()
        return r.json()
