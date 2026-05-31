#!/usr/bin/env python3
"""
Comprehensive test suite for all 4 completed enhancements.
Tests Enhancement 014, 020, 023, and 024.
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name: str, status: str, details: str = ""):
    """Print test result with color coding."""
    if status == "PASS":
        print(f"{Colors.GREEN}✓{Colors.END} {name}")
        if details:
            print(f"  {Colors.BLUE}→{Colors.END} {details}")
    elif status == "FAIL":
        print(f"{Colors.RED}✗{Colors.END} {name}")
        if details:
            print(f"  {Colors.RED}→{Colors.END} {details}")
    elif status == "SKIP":
        print(f"{Colors.YELLOW}⊘{Colors.END} {name}")
        if details:
            print(f"  {Colors.YELLOW}→{Colors.END} {details}")

def test_enhancement_024_cost_dashboard():
    """Test Enhancement 024: Real-Time Cost Tracking Dashboard"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}Enhancement 024: Cost Dashboard{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")

    # Test 1: Cost Summary
    try:
        response = requests.get(f"{BASE_URL}/api/costs/summary")
        if response.status_code == 200:
            data = response.json()
            print_test(
                "GET /api/costs/summary",
                "PASS",
                f"Total cost: ${data.get('total_cost', 0):.4f}, Requests: {data.get('request_count', 0)}"
            )
        else:
            print_test("GET /api/costs/summary", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        print_test("GET /api/costs/summary", "FAIL", str(e))

    # Test 2: Budgets
    try:
        response = requests.get(f"{BASE_URL}/api/costs/budgets")
        if response.status_code == 200:
            data = response.json()
            budget_count = len(data.get('budgets', []))
            print_test(
                "GET /api/costs/budgets",
                "PASS",
                f"Found {budget_count} budget(s)"
            )
            if budget_count > 0:
                budget = data['budgets'][0]
                print(f"    Budget: {budget.get('budget_name')} - {budget.get('provider', 'all')}")
        else:
            print_test("GET /api/costs/budgets", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        print_test("GET /api/costs/budgets", "FAIL", str(e))

    # Test 3: Alerts
    try:
        response = requests.get(f"{BASE_URL}/api/costs/alerts")
        if response.status_code == 200:
            data = response.json()
            alert_count = data.get('total_alerts', 0)
            print_test(
                "GET /api/costs/alerts",
                "PASS",
                f"Active alerts: {alert_count}"
            )
        else:
            print_test("GET /api/costs/alerts", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        print_test("GET /api/costs/alerts", "FAIL", str(e))

    # Test 4: Projections
    try:
        response = requests.get(f"{BASE_URL}/api/costs/projections")
        if response.status_code == 200:
            data = response.json()
            print_test(
                "GET /api/costs/projections",
                "PASS",
                f"Weekly: ${data['projections']['weekly']:.4f}, Monthly: ${data['projections']['monthly']:.4f}"
            )
        else:
            print_test("GET /api/costs/projections", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        print_test("GET /api/costs/projections", "FAIL", str(e))

def test_enhancement_023_developer_tools():
    """Test Enhancement 023: Developer Tools"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}Enhancement 023: Developer Tools{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")

    # Test 1: Debug Request
    try:
        payload = {
            "message": "Test debug request",
            "provider": None,
            "include_routing_decision": True,
            "include_context": True,
            "include_timing": True
        }
        response = requests.post(f"{BASE_URL}/api/dev/debug", json=payload)
        if response.status_code == 200:
            data = response.json()
            print_test(
                "POST /api/dev/debug",
                "PASS",
                f"Request ID: {data.get('request_id', 'N/A')}"
            )
        else:
            print_test("POST /api/dev/debug", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        print_test("POST /api/dev/debug", "FAIL", str(e))

    # Test 2: Test Provider
    try:
        payload = {
            "provider": "gemini",
            "test_message": "Hello, test!"
        }
        response = requests.post(f"{BASE_URL}/api/dev/test-provider", json=payload)
        if response.status_code == 200:
            data = response.json()
            print_test(
                "POST /api/dev/test-provider",
                "PASS",
                f"Provider: {data.get('provider', 'N/A')}, Success: {data.get('success', False)}"
            )
        else:
            print_test("POST /api/dev/test-provider", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        print_test("POST /api/dev/test-provider", "FAIL", str(e))

    # Test 3: Mock Mode Status
    try:
        response = requests.get(f"{BASE_URL}/api/dev/mock-mode")
        if response.status_code == 200:
            data = response.json()
            print_test(
                "GET /api/dev/mock-mode",
                "PASS",
                f"Mock mode enabled: {data.get('enabled', False)}"
            )
        else:
            print_test("GET /api/dev/mock-mode", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        print_test("GET /api/dev/mock-mode", "FAIL", str(e))

    # Test 4: Toggle Mock Mode (enable)
    try:
        payload = {"enabled": True}
        response = requests.post(f"{BASE_URL}/api/dev/mock-mode/toggle", json=payload)
        if response.status_code == 200:
            data = response.json()
            print_test(
                "POST /api/dev/mock-mode/toggle (enable)",
                "PASS",
                f"Mock mode: {data.get('enabled', False)}"
            )
        else:
            print_test("POST /api/dev/mock-mode/toggle", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        print_test("POST /api/dev/mock-mode/toggle", "FAIL", str(e))

    # Test 5: Toggle Mock Mode (disable)
    try:
        payload = {"enabled": False}
        response = requests.post(f"{BASE_URL}/api/dev/mock-mode/toggle", json=payload)
        if response.status_code == 200:
            data = response.json()
            print_test(
                "POST /api/dev/mock-mode/toggle (disable)",
                "PASS",
                f"Mock mode: {data.get('enabled', False)}"
            )
        else:
            print_test("POST /api/dev/mock-mode/toggle", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        print_test("POST /api/dev/mock-mode/toggle", "FAIL", str(e))

def test_enhancement_014_archive_system():
    """Test Enhancement 014: Session History & Project Archive"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}Enhancement 014: Archive System{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")

    # Test 1: List Archived Conversations
    try:
        response = requests.get(f"{BASE_URL}/api/archives/conversations")
        if response.status_code == 200:
            data = response.json()
            print_test(
                "GET /api/archives/conversations",
                "PASS",
                f"Found {data.get('total', 0)} archived conversation(s)"
            )
        else:
            print_test("GET /api/archives/conversations", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        print_test("GET /api/archives/conversations", "FAIL", str(e))

    # Test 2: List Archived Sessions
    try:
        response = requests.get(f"{BASE_URL}/api/archives/sessions")
        if response.status_code == 200:
            data = response.json()
            print_test(
                "GET /api/archives/sessions",
                "PASS",
                f"Found {data.get('total', 0)} archived session(s)"
            )
        else:
            print_test("GET /api/archives/sessions", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        print_test("GET /api/archives/sessions", "FAIL", str(e))

    # Test 3: List Project Archives
    try:
        response = requests.get(f"{BASE_URL}/api/archives/projects")
        if response.status_code == 200:
            data = response.json()
            print_test(
                "GET /api/archives/projects",
                "PASS",
                f"Found {data.get('total', 0)} project archive(s)"
            )
        else:
            print_test("GET /api/archives/projects", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        print_test("GET /api/archives/projects", "FAIL", str(e))

    # Test 4: Search Archives
    try:
        response = requests.get(f"{BASE_URL}/api/archives/search?q=test")
        if response.status_code == 200:
            data = response.json()
            total_results = sum(len(v) for v in data.values() if isinstance(v, list))
            print_test(
                "GET /api/archives/search",
                "PASS",
                f"Found {total_results} result(s) for 'test'"
            )
        else:
            print_test("GET /api/archives/search", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        print_test("GET /api/archives/search", "FAIL", str(e))

    # Test 5: Archive Statistics
    try:
        response = requests.get(f"{BASE_URL}/api/archives/stats")
        if response.status_code == 200:
            data = response.json()
            print_test(
                "GET /api/archives/stats",
                "PASS",
                f"Total archives: {data.get('total_archives', 0)}, Storage: {data.get('storage_used_mb', 0):.2f}MB"
            )
        else:
            print_test("GET /api/archives/stats", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        print_test("GET /api/archives/stats", "FAIL", str(e))

    # Test 6: Export Archives
    try:
        response = requests.get(f"{BASE_URL}/api/archives/export?collection=conversations&format=json")
        if response.status_code == 200:
            data = response.json()
            print_test(
                "GET /api/archives/export",
                "PASS",
                f"Exported {data.get('record_count', 0)} record(s) as JSON"
            )
        else:
            print_test("GET /api/archives/export", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        print_test("GET /api/archives/export", "FAIL", str(e))

def test_enhancement_020_clickhouse():
    """Test Enhancement 020: ClickHouse Integration"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}Enhancement 020: ClickHouse Integration{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")

    # Test 1: ClickHouse HTTP API
    try:
        response = requests.get("http://localhost:8123/")
        if response.status_code == 200 and "Ok." in response.text:
            print_test(
                "ClickHouse HTTP API (port 8123)",
                "PASS",
                "Server responding"
            )
        else:
            print_test("ClickHouse HTTP API", "FAIL", f"Unexpected response: {response.text[:50]}")
    except Exception as e:
        print_test("ClickHouse HTTP API", "SKIP", "ClickHouse not running (docker-compose up in monitoring-hub)")

    # Test 2: Check Database
    try:
        response = requests.get("http://localhost:8123/?query=SHOW+DATABASES")
        if response.status_code == 200:
            databases = response.text.strip().split('\n')
            has_tempo = 'tempo' in databases
            status = "PASS" if has_tempo else "FAIL"
            print_test(
                "ClickHouse tempo database",
                status,
                f"Found databases: {', '.join(databases[:5])}"
            )
        else:
            print_test("ClickHouse database check", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        print_test("ClickHouse database check", "SKIP", str(e))

    # Test 3: Check Tables
    try:
        response = requests.get("http://localhost:8123/?query=SHOW+TABLES+FROM+tempo")
        if response.status_code == 200:
            tables = response.text.strip().split('\n')
            expected_tables = ['traces', 'trace_index', 'service_operations']
            has_all = all(table in tables for table in expected_tables)
            status = "PASS" if has_all else "FAIL"
            print_test(
                "ClickHouse table schema",
                status,
                f"Tables: {', '.join(tables)}"
            )
        else:
            print_test("ClickHouse table check", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        print_test("ClickHouse table check", "SKIP", str(e))

    # Test 4: Query Trace Count
    try:
        response = requests.get("http://localhost:8123/?query=SELECT+COUNT(*)+FROM+tempo.traces")
        if response.status_code == 200:
            count = int(response.text.strip())
            print_test(
                "ClickHouse trace storage",
                "PASS",
                f"Total traces stored: {count:,}"
            )
        else:
            print_test("ClickHouse trace count", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        print_test("ClickHouse trace count", "SKIP", str(e))

    # Test 5: Tempo Integration
    try:
        response = requests.get("http://localhost:3201/ready")
        if response.status_code == 200:
            print_test(
                "Grafana Tempo readiness",
                "PASS",
                "Tempo is ready"
            )
        else:
            print_test("Grafana Tempo", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        print_test("Grafana Tempo", "SKIP", "Tempo not running (start monitoring-hub)")

def main():
    """Run all enhancement tests."""
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.END}")
    print(f"{Colors.YELLOW}AI Orchestrator - Enhancement Test Suite{Colors.END}")
    print(f"{Colors.YELLOW}Testing Enhancements 014, 020, 023, 024{Colors.END}")
    print(f"{Colors.YELLOW}{'='*60}{Colors.END}")

    # Check if backend is running
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=2)
        if response.status_code != 200:
            print(f"\n{Colors.RED}ERROR: Backend not responding at {BASE_URL}{Colors.END}")
            print(f"{Colors.YELLOW}Please start: ./venv/bin/uvicorn src.api.main:app --reload{Colors.END}\n")
            return
    except Exception as e:
        print(f"\n{Colors.RED}ERROR: Cannot connect to backend at {BASE_URL}{Colors.END}")
        print(f"{Colors.YELLOW}Please start: ./venv/bin/uvicorn src.api.main:app --reload{Colors.END}\n")
        return

    # Run all tests
    test_enhancement_024_cost_dashboard()
    test_enhancement_023_developer_tools()
    test_enhancement_014_archive_system()
    test_enhancement_020_clickhouse()

    print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}Test Suite Complete{Colors.END}")
    print(f"{Colors.GREEN}{'='*60}{Colors.END}\n")
    print(f"{Colors.BLUE}Frontend URLs:{Colors.END}")
    print(f"  • Cost Dashboard: http://localhost:5173/#/costs")
    print(f"  • Dev Tools: http://localhost:5173/#/dev-tools")
    print(f"{Colors.BLUE}Backend URLs:{Colors.END}")
    print(f"  • API Docs: http://localhost:8000/docs")
    print(f"  • ClickHouse: http://localhost:8123/")
    print(f"  • Grafana Tempo: http://localhost:3201/")
    print()

if __name__ == "__main__":
    main()
