#!/usr/bin/env python3
"""
Docker Compose E2E test template for FastAPI-based projects.
Brings up the full stack, waits for health, runs the benchmark workflow
against real Docker services, captures logs on failure, tears down.
"""
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error

COMPOSE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3008"
TIMEOUT = 60


def run(cmd, check=True, timeout_val=30):
    result = subprocess.run(cmd, shell=True, capture_output=True,
        text=True, timeout=timeout_val, cwd=COMPOSE_DIR)
    if check and result.returncode != 0:
        print(f"FAILED: {cmd}")
        print(result.stdout[-500:])
        print(result.stderr[-500:])
        sys.exit(result.returncode)
    return result


def wait_for_health(url, timeout_sec=TIMEOUT):
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            resp = urllib.request.urlopen(url, timeout=5)
            if resp.status == 200:
                return True
        except (urllib.error.URLError, TimeoutError, ConnectionRefusedError):
            pass
        time.sleep(2)
    return False


def api_get(path):
    resp = urllib.request.urlopen(f"{BACKEND_URL}{path}", timeout=10)
    return json.loads(resp.read())


def api_post(path, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(f"{BACKEND_URL}{path}", data=body,
        headers={"Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=10)
    return json.loads(resp.read())


def poll_benchmark(benchmark_id, timeout_sec=30):
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        data = api_get(f"/api/benchmarks/{benchmark_id}")
        if data["status"] == "completed":
            return data
        time.sleep(1)
    raise TimeoutError(f"Benchmark {benchmark_id} not completed in {timeout_sec}s")


def main():
    step = 1
    failures = []

    def check(description, condition, detail=""):
        nonlocal step
        status = "PASS" if condition else "FAIL"
        print(f"  [{step}] {status}: {description} {detail}")
        if not condition:
            failures.append(description)
        step += 1

    # ---- Setup ----
    print("\n=== Docker Compose E2E Test ===\n")

    print("Bringing up Docker stack...")
    run("docker compose up -d --wait --wait-timeout 60", timeout_val=90)
    print("  Stack started.")

    # ---- Health Checks ----
    print("\nHealth checks...")
    check("Backend /health", wait_for_health(f"{BACKEND_URL}/health"))
    check("Frontend serves", wait_for_health(FRONTEND_URL))

    # ---- Seed Data ----
    print("\nSeed data...")
    try:
        api_post("/api/models/seed-defaults", {})
        check("Seed models", True)
    except Exception as e:
        check("Seed models", False, str(e))
    try:
        api_post("/api/test-cases/seed-defaults", {})
        check("Seed test cases", True)
    except Exception as e:
        check("Seed test cases", False, str(e))

    # ---- Benchmark Workflow ----
    if not failures:
        print("\nBenchmark workflow...")
        try:
            model_names = [m["name"] for m in api_get("/api/models/")][:2]
            case_names = [c["name"] for c in api_get("/api/test-cases/")][:2]
            benchmark = api_post("/api/benchmarks/", {
                "name": "docker-e2e-test",
                "model_names": model_names,
                "test_case_names": case_names,
                "use_mock": True,
            })
            check("Benchmark created", benchmark["status"] == "pending")

            completed = poll_benchmark(benchmark["id"])
            check("Benchmark completed", completed["status"] == "completed")

            results = api_get(f"/api/results/benchmark/{benchmark['id']}")
            check("Results exist", len(results) > 0)
            check("All completed", all(r["status"] == "completed" for r in results))
        except Exception as e:
            check("Benchmark workflow", False, str(e))

    # ---- Summary ----
    total = step - 1
    passed = total - len(failures)
    print(f"\n{'='*40}")
    print(f"Results: {passed}/{total} passed")
    if failures:
        run("docker compose logs backend --tail 50 > /tmp/docker-e2e-backend.log", check=False)
        print("Logs saved to /tmp/docker-e2e-*.log")
    else:
        print("All checks passed!")

    # ---- Teardown ----
    print("\nTearing down...")
    run("docker compose down -v", check=False)
    print("Done.")
    sys.exit(0 if not failures else 1)


if __name__ == "__main__":
    main()
