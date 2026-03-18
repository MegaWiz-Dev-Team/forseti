# SI-04: Test Script — Sprint 04
# ⚖️ Forseti — Sprint 04 TDD Test Cases

| รายการ | รายละเอียด |
|---|---|
| **เอกสาร** | SI-04-SP04 |
| **Sprint** | Sprint 04 — Multi-Project + Dashboard + Self-Test |
| **วันที่** | 2026-03-17 |
| **จำนวน Test Cases** | 16 (unit) |
| **ผลการทดสอบ** | ✅ 87/87 total pass |

---

## 1. Unit Tests — Multi-Project Config (6 tests)

| # | Test Case | Module | Expected | Result |
|---|---|---|---|---|
| SP04-01 | load_forseti_yaml | config | Parse 3 projects | ✅ PASS |
| SP04-02 | project_filter_by_name | config | Filter by project key | ✅ PASS |
| SP04-03 | cli_project_flag | cli | --project selects target | ✅ PASS |
| SP04-04 | default_all_projects | orchestrator | No flag → run all | ✅ PASS |
| SP04-05 | suite_name_per_project | orchestrator | Separate suite per project | ✅ PASS |
| SP04-06 | yaml_path_per_project | config | Correct YAML path | ✅ PASS |

## 2. Unit Tests — Dashboard (5 tests)

| # | Test Case | Module | Expected | Result |
|---|---|---|---|---|
| SP04-07 | dashboard_serves_html | dashboard | GET / → 200 HTML | ✅ PASS |
| SP04-08 | api_runs_json | dashboard | GET /api/runs → JSON | ✅ PASS |
| SP04-09 | api_run_detail | dashboard | GET /api/runs/1 → runs + scenarios | ✅ PASS |
| SP04-10 | api_trend | dashboard | GET /api/trend → JSON array | ✅ PASS |
| SP04-11 | api_suites | dashboard | GET /api/suites → list | ✅ PASS |

## 3. Unit Tests — Forseti Self-Test (5 tests)

| # | Test Case | Module | Expected | Result |
|---|---|---|---|---|
| SP04-12 | selftest_dashboard_loaded | self_test | Title contains "Forseti" | ✅ PASS |
| SP04-13 | selftest_api_health | self_test | /api/suites → 200 | ✅ PASS |
| SP04-14 | selftest_runs_endpoint | self_test | /api/runs → JSON array | ✅ PASS |
| SP04-15 | selftest_trend_endpoint | self_test | /api/trend → JSON array | ✅ PASS |
| SP04-16 | selftest_static_assets | self_test | CSS + JS load correctly | ✅ PASS |
