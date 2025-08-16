import os
import json
import time
import re
import asyncio
from pathlib import Path
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

PORT = int(os.getenv("PORT", "4000"))
CORS_ORIGIN = os.getenv("CORS_ORIGIN", "*")
LATENCY_MS = int(os.getenv("LATENCY_MS", "0"))
RESP_HEADERS_PREFIX = "RESP_HEADERS_"
FIXTURES_DIR = Path("./fixtures")
SAFE_HEAD = re.compile(r"^[A-Za-z0-9._-]+$")  # ← 先頭要素の安全文字セット

app = FastAPI()

# CORS
if CORS_ORIGIN.strip() == "*":
    origins = ["*"]
    allow_credentials = False  # ← ワイルドカード時は False
else:
    origins = [o.strip() for o in CORS_ORIGIN.split(",") if o.strip()]
    allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CustomHeaderMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.response_headers = {
            key[len(RESP_HEADERS_PREFIX):].replace("_", "-"): val
            for key, val in os.environ.items()
            if key.startswith(RESP_HEADERS_PREFIX)
        }

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        for name, value in self.response_headers.items():
            response.headers[name] = value
        return response

app.add_middleware(CustomHeaderMiddleware)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        started = time.time()
        try:
            response = await call_next(request)
        except Exception as e:
            # 例外もログに残す
            dur = (time.time() - started) * 1000
            print(f"{int(time.time())} {request.method} {request.url.path} 500 {dur:.2f}ms EXC:{type(e).__name__}")
            raise
        dur = (time.time() - started) * 1000
        print(f"{int(time.time())} {request.method} {request.url.path} {response.status_code} {dur:.2f}ms")
        return response

app.add_middleware(LoggingMiddleware)

@app.get("/healthz")
async def healthz():
    return {"ok": True}

@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def catch_all(full_path: str, request: Request):
    if LATENCY_MS > 0:
        await asyncio.sleep(LATENCY_MS / 1000)

    segments = [seg for seg in full_path.strip("/").split("/") if seg]
    head = segments[0] if segments else ""

    # ステータスショートカット（数字のみ）
    if head.isdigit():
        code = int(head)
        return JSONResponse(status_code=code, content={"status": code, "path": f"/{full_path}"})

    # 先頭要素バリデーション
    if not head or not SAFE_HEAD.match(head):
        return JSONResponse(status_code=404, content={"error": "file not found", "head": head})

    # ファイル解決
    base = FIXTURES_DIR / head
    candidates = [base.with_suffix(".json"), base.with_suffix(".html"), base.with_suffix(".txt")]
    found = next((c for c in candidates if c.is_file()), None)
    if not found:
        # 任意拡張子
        for f in FIXTURES_DIR.glob(f"{head}.*"):
            if f.is_file():
                found = f
                break
    if not found:
        return JSONResponse(status_code=404, content={"error": "file not found", "head": head})

    ext = found.suffix.lower()
    try:
        if ext == ".json":
            with found.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return JSONResponse(content=data, media_type="application/json; charset=utf-8")
        elif ext == ".html":
            with found.open("r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read(), media_type="text/html; charset=utf-8")
        elif ext == ".txt":
            with found.open("r", encoding="utf-8") as f:
                return PlainTextResponse(content=f.read(), media_type="text/plain; charset=utf-8")
        else:
            with found.open("rb") as f:
                return Response(content=f.read(), media_type="application/octet-stream")
    except json.JSONDecodeError:
        return PlainTextResponse(status_code=500, content="Error: Malformed JSON file")
    except Exception as e:
        # 読み取り系失敗も 500
        return PlainTextResponse(status_code=500, content=f"Error: {type(e).__name__}")
