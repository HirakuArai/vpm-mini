#!/usr/bin/env python3

import json
import subprocess
import sys
import time
import statistics
from datetime import datetime, timezone
from pathlib import Path
import requests
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings for development
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


def run_command(cmd, shell=True):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(
            cmd, shell=shell, capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {cmd}")
        print(f"Error: {e.stderr}")
        return None


def log_info(message):
    print(f"\033[32m[INFO]\033[0m {message}")


def log_warn(message):
    print(f"\033[33m[WARN]\033[0m {message}")


def log_error(message):
    print(f"\033[31m[ERROR]\033[0m {message}")


def check_argo_app_status():
    """Check Argo CD Application status"""
    log_info("Checking root-app Application status...")

    app_json_str = run_command("kubectl -n argocd get application root-app -o json")
    if not app_json_str:
        log_error("Failed to get root-app Application")
        return False, False, None

    try:
        app_json = json.loads(app_json_str)
        sync_status = (
            app_json.get("status", {}).get("sync", {}).get("status", "Unknown")
        )
        health_status = (
            app_json.get("status", {}).get("health", {}).get("status", "Unknown")
        )

        synced = sync_status == "Synced"
        healthy = health_status == "Healthy"

        if synced:
            log_info("✅ root-app is Synced")
        else:
            log_warn(f"⚠️  root-app sync status: {sync_status}")

        if healthy:
            log_info("✅ root-app is Healthy")
        else:
            log_warn(f"⚠️  root-app health status: {health_status}")

        return synced, healthy, app_json

    except json.JSONDecodeError as e:
        log_error(f"Failed to parse Application JSON: {e}")
        return False, False, None


def check_httproute_config():
    """Check HTTPRoute configuration for canary weights"""
    log_info("Checking HTTPRoute canary configuration...")

    httproute_json_str = run_command(
        "kubectl -n hyper-swarm get httproute hello-route -o json"
    )
    if not httproute_json_str:
        log_warn("Failed to get HTTPRoute hello-route")
        return 0, 0

    try:
        httproute_json = json.loads(httproute_json_str)
        rules = httproute_json.get("spec", {}).get("rules", [])

        hello_weight = 0
        v2_weight = 0

        if rules:
            backend_refs = rules[0].get("backendRefs", [])
            for ref in backend_refs:
                name = ref.get("name", "")
                weight = ref.get("weight", 0)

                if name == "hello":
                    hello_weight = weight
                elif name == "hello-v2":
                    v2_weight = weight

        log_info(f"HTTPRoute weights: hello={hello_weight}, hello-v2={v2_weight}")
        return hello_weight, v2_weight

    except json.JSONDecodeError as e:
        log_error(f"Failed to parse HTTPRoute JSON: {e}")
        return 0, 0


def perform_canary_test(
    url="http://localhost:31380/hello", num_requests=300, timeout=2
):
    """Perform canary testing with traffic distribution analysis"""
    log_info(f"Performing canary test: {num_requests} requests to {url}")

    hello_count = 0
    v2_count = 0
    error_count = 0
    latencies = []

    for i in range(num_requests):
        if (i + 1) % 50 == 0:
            log_info(f"Progress: {i + 1}/{num_requests} requests")

        start_time = time.time()

        try:
            response = requests.get(url, timeout=timeout, verify=False)
            end_time = time.time()
            latency_ms = int((end_time - start_time) * 1000)
            latencies.append(latency_ms)

            if response.status_code == 200:
                content = response.text.strip()
                # Check for TARGET=v2 in response (hello-v2 service)
                if "v2" in content or "TARGET=v2" in content:
                    v2_count += 1
                else:
                    hello_count += 1
            else:
                error_count += 1

        except requests.exceptions.RequestException:
            error_count += 1
            # Still record latency for timeout cases
            end_time = time.time()
            latency_ms = int((end_time - start_time) * 1000)
            latencies.append(latency_ms)

        # Brief pause to avoid overwhelming
        time.sleep(0.01)

    # Calculate metrics
    total_success = hello_count + v2_count
    v2_share = v2_count / total_success if total_success > 0 else 0
    p50_ms = int(statistics.median(latencies)) if latencies else 0

    log_info("Canary test results:")
    log_info(f"  Total requests: {num_requests}")
    log_info(f"  Successful responses: {total_success}")
    log_info(f"  Hello (v1) responses: {hello_count}")
    log_info(f"  Hello-v2 responses: {v2_count}")
    log_info(f"  V2 share: {v2_share:.3f} ({v2_share * 100:.1f}%)")
    log_info(f"  Error responses: {error_count}")
    log_info(f"  P50 latency: {p50_ms}ms")

    # Check if v2 share is within expected range (5-20%)
    v2_in_range = 0.05 <= v2_share <= 0.20
    if v2_in_range:
        log_info("✅ V2 share within expected range (5-20%)")
    else:
        log_warn(
            f"⚠️  V2 share outside expected range: {v2_share:.3f} (expected: 0.05-0.20)"
        )

    return {
        "total_requests": num_requests,
        "hello_count": hello_count,
        "v2_count": v2_count,
        "error_count": error_count,
        "v2_share": round(v2_share, 3),
        "p50_ms": p50_ms,
        "v2_in_range": v2_in_range,
    }


def generate_snapshot_report(template_path, output_path, variables):
    """Generate snapshot report from template"""
    if not template_path.exists():
        log_warn(f"Template file not found: {template_path}")
        return

    log_info(f"Generating snapshot report: {output_path}")

    try:
        template_content = template_path.read_text()

        # Replace template variables
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            template_content = template_content.replace(placeholder, str(value))

        output_path.write_text(template_content)
        log_info(f"Snapshot report generated: {output_path}")

    except Exception as e:
        log_error(f"Failed to generate snapshot report: {e}")


def main():
    print("=" * 40)
    print("Phase 4-5: Canary Deployment Verification")
    print("=" * 40)

    project_root = Path(__file__).parent.parent
    reports_dir = project_root / "reports"
    reports_dir.mkdir(exist_ok=True)

    # Initialize results
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "commit": run_command("git rev-parse --short HEAD") or "unknown",
        "branch": run_command("git branch --show-current") or "unknown",
    }

    # 1) Check Argo CD Application status
    synced, healthy, app_json = check_argo_app_status()
    results["synced"] = synced
    results["healthy"] = healthy

    # 2) Check HTTPRoute configuration
    hello_weight, v2_weight = check_httproute_config()
    results["hello_weight"] = hello_weight / 100.0 if hello_weight else 0
    results["v2_weight"] = v2_weight / 100.0 if v2_weight else 0

    # 3) Perform canary testing
    canary_results = perform_canary_test()
    results.update(canary_results)

    # 4) Generate JSON results
    output_json = reports_dir / "phase4_canary_verify.json"

    final_results = {
        "timestamp": results["timestamp"],
        "commit": results["commit"],
        "branch": results["branch"],
        "argo_status": {"synced": results["synced"], "healthy": results["healthy"]},
        "httproute_config": {
            "hello_weight": results["hello_weight"],
            "v2_weight": results["v2_weight"],
        },
        "canary_test": {
            "total_requests": results["total_requests"],
            "hello_count": results["hello_count"],
            "v2_count": results["v2_count"],
            "error_count": results["error_count"],
            "v2_share": results["v2_share"],
            "p50_ms": results["p50_ms"],
        },
        "verification": {
            "synced": results["synced"],
            "healthy": results["healthy"],
            "hello_weight": results["hello_weight"],
            "v2_weight": results["v2_weight"],
            "v2_share": results["v2_share"],
            "p50_ms": results["p50_ms"],
            "v2_in_range": results["v2_in_range"],
            "all_ok": (
                results["synced"]
                and results["healthy"]
                and results["v2_in_range"]
                and results["p50_ms"] < 1000
            ),
        },
    }

    with open(output_json, "w") as f:
        json.dump(final_results, f, indent=2)

    log_info(f"Results saved to: {output_json}")

    # 5) Generate snapshot report
    template_path = (
        project_root / "reports" / "templates" / "phase4_canary_report.md.tmpl"
    )
    snapshot_path = reports_dir / "snap_phase4-5-canary-ready.md"

    template_vars = {
        "DATE": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "COMMIT": results["commit"],
        "VERIFY_JSON": "reports/phase4_canary_verify.json",
        "SYNCED": str(results["synced"]).lower(),
        "HEALTHY": str(results["healthy"]).lower(),
        "HELLO_WEIGHT": results["hello_weight"],
        "V2_WEIGHT": results["v2_weight"],
        "V2_SHARE": results["v2_share"],
        "P50_MS": results["p50_ms"],
        "HELLO_COUNT": results["hello_count"],
        "V2_COUNT": results["v2_count"],
        "TOTAL_REQUESTS": results["total_requests"],
        "V2_PERCENTAGE": f"{results['v2_share'] * 100:.1f}",
        "SUCCESS_COUNT": results["hello_count"] + results["v2_count"],
    }

    generate_snapshot_report(template_path, snapshot_path, template_vars)

    # 6) Summary and exit
    print("\n" + "=" * 40)
    print("Canary Verification Summary")
    print("=" * 40)

    all_ok = final_results["verification"]["all_ok"]

    if all_ok:
        log_info("✅ Phase 4-5 Canary deployment verification PASSED")
        log_info("   - root-app: Synced & Healthy")
        log_info(
            f"   - HTTPRoute: hello({results['hello_weight']:.1f}) / hello-v2({results['v2_weight']:.1f})"
        )
        log_info(
            f"   - Traffic distribution: v2_share ≈ {results['v2_share']:.3f} (5-20% range)"
        )
        log_info(f"   - Performance: P50 {results['p50_ms']}ms < 1000ms")
        log_info("   - Canary deployment successfully established")

        print(
            f"\n[OK] Canary verify complete: v2_share={results['v2_share']:.3f}, p50={results['p50_ms']}ms"
        )
        sys.exit(0)

    else:
        log_error("❌ Phase 4-5 Canary deployment verification FAILED")
        if not results["synced"]:
            log_error("   - root-app not synced")
        if not results["healthy"]:
            log_error("   - root-app not healthy")
        if not results["v2_in_range"]:
            log_error(
                f"   - V2 share out of range: {results['v2_share']:.3f} (expected: 0.05-0.20)"
            )
        if results["p50_ms"] >= 1000:
            log_error(f"   - P50 latency too high: {results['p50_ms']}ms")

        print(
            f"\n[FAIL] Canary verify: v2_share={results['v2_share']:.3f}, p50={results['p50_ms']}ms"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
