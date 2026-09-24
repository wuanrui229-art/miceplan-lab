from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .config import load_local_env
from .models import HallLayout, ModelError
from .parser import DeterministicBaselineParser, OpenAICompatibleStructuredParser
from .repository import InMemoryRepository, RepositoryError
from .service import MICEPlanService, ServiceError


def build_service(data_path: Path | None = None) -> MICEPlanService:
    load_local_env()
    path = data_path or Path(__file__).resolve().parents[1] / "data" / "demo_hall_v1.json"
    layout = HallLayout.from_dict(json.loads(path.read_text(encoding="utf-8")))
    parser_mode = os.getenv("MICEPLAN_PARSER", "baseline").lower()
    if parser_mode == "llm":
        required = ["MICEPLAN_LLM_ENDPOINT", "MICEPLAN_LLM_API_KEY", "MICEPLAN_LLM_MODEL"]
        missing = [name for name in required if not os.getenv(name)]
        if missing:
            raise RuntimeError(f"Missing LLM configuration: {', '.join(missing)}")
        parser = OpenAICompatibleStructuredParser(
            endpoint=os.environ["MICEPLAN_LLM_ENDPOINT"],
            api_key=os.environ["MICEPLAN_LLM_API_KEY"],
            model=os.environ["MICEPLAN_LLM_MODEL"],
            temperature=float(os.getenv("MICEPLAN_LLM_TEMPERATURE", "0")),
        )
    else:
        parser = DeterministicBaselineParser()
    return MICEPlanService(InMemoryRepository("demo", layout), parser)


def dispatch(service: MICEPlanService, method: str, path: str, payload: dict | None = None) -> tuple[int, dict | list]:
    payload = payload or {}
    if method == "OPTIONS":
        return 204, {}
    if method == "GET" and path == "/health":
        return 200, {"status": "ok"}
    if method == "GET" and path == "/projects/demo/versions":
        return 200, {"versions": service.list_versions("demo")}
    if method == "POST" and path == "/projects/demo/preview":
        proposal = service.preview("demo", str(payload.get("source_version", "v1")), str(payload.get("request", "")))
        return 200, proposal.to_dict()
    parts = path.strip("/").split("/")
    if method == "POST" and len(parts) == 3 and parts[0] == "proposals" and parts[2] in {"approve", "reject"}:
        proposal = service.approve(parts[1]) if parts[2] == "approve" else service.reject(parts[1])
        return 200, proposal.to_dict()
    return 404, {"error": "not_found"}


def make_handler(service: MICEPlanService):
    class Handler(BaseHTTPRequestHandler):
        server_version = "MICEPlanResearchAPI/0.1"

        def _send(self, status: int, payload: dict | list):
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.end_headers()
            self.wfile.write(body)

        def _json_body(self) -> dict:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0:
                return {}
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("JSON body must be an object")
            return payload

        def do_OPTIONS(self):
            status, response = dispatch(service, "OPTIONS", urlparse(self.path).path)
            self._send(status, response)

        def do_GET(self):
            path = urlparse(self.path).path
            try:
                status, response = dispatch(service, "GET", path)
                self._send(status, response)
            except (ModelError, RepositoryError, ServiceError) as exc:
                self._send(400, {"error": type(exc).__name__, "message": str(exc)})

        def do_POST(self):
            path = urlparse(self.path).path
            try:
                payload = self._json_body()
                status, response = dispatch(service, "POST", path, payload)
                self._send(status, response)
            except (ValueError, json.JSONDecodeError, ModelError, RepositoryError, ServiceError) as exc:
                self._send(400, {"error": type(exc).__name__, "message": str(exc)})

        def log_message(self, format: str, *args):
            if os.getenv("MICEPLAN_HTTP_LOG") == "1":
                super().log_message(format, *args)

    return Handler


def run(host: str = "127.0.0.1", port: int = 8765):
    service = build_service()
    server = ThreadingHTTPServer((host, port), make_handler(service))
    print(f"MICEPlan research API listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run(port=int(os.getenv("PORT", "8765")))
