#!/usr/bin/env python3
"""
Stress test for Brutally Honest AI uploads.

Designed to run on a Jetson/NVIDIA host (or any host) to validate:
- Multiple concurrent uploads (documents/audio)
- Large-file rejection behavior without OOM
- Queue endpoints and document upload endpoints

Examples:
  python scripts/stress_test_uploads.py --base-url http://localhost:8000 --api-key "$API_MASTER_KEY" --mode documents --count 50 --concurrency 10 --size-mb 1
  python scripts/stress_test_uploads.py --base-url http://localhost:8000 --api-key "$API_MASTER_KEY" --mode queue-documents --count 50 --concurrency 10 --size-mb 1
  python scripts/stress_test_uploads.py --base-url http://localhost:8000 --api-key "$API_MASTER_KEY" --mode huge-documents --count 5 --concurrency 2 --size-mb 200
"""

from __future__ import annotations

import argparse
import asyncio
import os
import random
import string
import time
from dataclasses import dataclass
from typing import Optional

import httpx


def _rand_id(n: int = 8) -> str:
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


def _payload_bytes(size_mb: float) -> bytes:
    size = int(size_mb * 1024 * 1024)
    # Deterministic-ish content (compressible, but fine for upload stress).
    chunk = (b"BrutallyHonestAI" * 1024)[:4096]
    out = bytearray()
    while len(out) < size:
        out.extend(chunk)
    return bytes(out[:size])


@dataclass
class Result:
    ok: bool
    status_code: int
    elapsed_s: float
    error: Optional[str] = None


async def _upload_document(client: httpx.AsyncClient, base_url: str, api_key: str, size_mb: float) -> Result:
    filename = f"stress_{_rand_id()}.txt"
    data = _payload_bytes(size_mb)
    t0 = time.time()
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        r = await client.post(
            f"{base_url}/documents/upload",
            headers=headers,
            files={"file": (filename, data, "text/plain")},
            timeout=120,
        )
        elapsed = time.time() - t0
        ok = r.status_code == 200 and r.json().get("success") is True
        return Result(ok=ok, status_code=r.status_code, elapsed_s=elapsed, error=None if ok else r.text[:200])
    except Exception as e:
        return Result(ok=False, status_code=0, elapsed_s=time.time() - t0, error=str(e))


async def _queue_document(client: httpx.AsyncClient, base_url: str, api_key: str, size_mb: float, device_id: str) -> Result:
    filename = f"stress_{_rand_id()}.txt"
    data = _payload_bytes(size_mb)
    t0 = time.time()
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        r = await client.post(
            f"{base_url}/queue/upload/document",
            headers=headers,
            files={"file": (filename, data, "text/plain")},
            data={"device_id": device_id, "priority": "normal"},
            timeout=120,
        )
        elapsed = time.time() - t0
        ok = r.status_code == 200 and r.json().get("success") is True
        return Result(ok=ok, status_code=r.status_code, elapsed_s=elapsed, error=None if ok else r.text[:200])
    except Exception as e:
        return Result(ok=False, status_code=0, elapsed_s=time.time() - t0, error=str(e))


async def _queue_audio(client: httpx.AsyncClient, base_url: str, api_key: str, size_mb: float, device_id: str) -> Result:
    # Not a real WAV; the goal is upload-path stress and size rejection behavior.
    filename = f"stress_{_rand_id()}.wav"
    data = _payload_bytes(size_mb)
    t0 = time.time()
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        r = await client.post(
            f"{base_url}/queue/upload/transcription",
            headers=headers,
            files={"file": (filename, data, "audio/wav")},
            data={"device_id": device_id, "priority": "normal"},
            timeout=120,
        )
        elapsed = time.time() - t0
        ok = r.status_code == 200 and r.json().get("success") is True
        return Result(ok=ok, status_code=r.status_code, elapsed_s=elapsed, error=None if ok else r.text[:200])
    except Exception as e:
        return Result(ok=False, status_code=0, elapsed_s=time.time() - t0, error=str(e))


async def run() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", default=os.environ.get("BH_BASE_URL", "http://localhost:8000"))
    p.add_argument("--api-key", default=os.environ.get("BH_API_KEY", ""))
    p.add_argument("--mode", choices=["documents", "queue-documents", "queue-audio", "huge-documents"], required=True)
    p.add_argument("--count", type=int, default=50)
    p.add_argument("--concurrency", type=int, default=10)
    p.add_argument("--size-mb", type=float, default=1.0)
    p.add_argument("--device-id", default="stress_tester")
    args = p.parse_args()

    # API key is required for remote/external calls, but not needed when running locally on the server
    # because the API allows internal requests from 127.0.0.1.

    # huge-documents is meant to validate rejection without OOM; it reuses documents endpoint.
    size_mb = args.size_mb
    # If caller didn't override --size-mb (left at default 1MB), bump to a "huge" default.
    if args.mode == "huge-documents" and args.size_mb == 1.0:
        size_mb = 200.0

    limiter = asyncio.Semaphore(args.concurrency)
    results: list[Result] = []

    async with httpx.AsyncClient() as client:
        # quick health check
        r = await client.get(f"{args.base_url}/health", timeout=10)
        if r.status_code != 200:
            raise SystemExit(f"Health check failed: {r.status_code} {r.text[:120]}")

        async def one(i: int):
            async with limiter:
                if args.mode == "documents":
                    return await _upload_document(client, args.base_url, args.api_key, size_mb)
                if args.mode == "queue-documents":
                    return await _queue_document(client, args.base_url, args.api_key, size_mb, args.device_id)
                if args.mode == "queue-audio":
                    return await _queue_audio(client, args.base_url, args.api_key, size_mb, args.device_id)
                if args.mode == "huge-documents":
                    return await _upload_document(client, args.base_url, args.api_key, size_mb)
                raise RuntimeError("unknown mode")

        t0 = time.time()
        tasks = [asyncio.create_task(one(i)) for i in range(args.count)]
        for t in asyncio.as_completed(tasks):
            results.append(await t)
        total = time.time() - t0

    oks = [r for r in results if r.ok]
    fails = [r for r in results if not r.ok]
    lat = sorted(r.elapsed_s for r in results)
    p50 = lat[int(len(lat) * 0.50)] if lat else 0
    p95 = lat[int(len(lat) * 0.95) - 1] if lat else 0

    print("")
    print("=== Stress Test Results ===")
    print(f"mode={args.mode} count={args.count} concurrency={args.concurrency} size_mb={size_mb}")
    print(f"ok={len(oks)} fail={len(fails)} total_time_s={total:.2f} rps={args.count/total:.2f}")
    print(f"latency_s p50={p50:.3f} p95={p95:.3f} max={max(lat) if lat else 0:.3f}")
    if fails:
        # show a small sample of failures
        sample = fails[:5]
        print("failures(sample):")
        for f in sample:
            print(f"- status={f.status_code} t={f.elapsed_s:.2f}s err={f.error}")

    # For huge-documents we expect mostly failures (400).
    if args.mode == "huge-documents":
        expected_fail = sum(1 for r in results if r.status_code == 400)
        if expected_fail == 0:
            print("WARNING: huge-documents produced no 400 responses; check size limits.")
        return 0

    return 0 if not fails else 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run()))

