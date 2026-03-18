# SI-04: Test Script — Sprint 05
# ⚖️ Forseti — Sprint 05 TDD Test Cases

| รายการ | รายละเอียด |
|---|---|
| **เอกสาร** | SI-04-SP05 |
| **Sprint** | Sprint 05 — UI Testing + DB Verification + Version Auto-Detect |
| **วันที่** | 2026-03-18 |
| **จำนวน Test Cases** | 7 (unit) |
| **ผลการทดสอบ** | ✅ 94/94 total pass |

---

## 1. Unit Tests — UI Testing via YAML (4 tests)

| # | Test Case | Module | Expected | Result |
|---|---|---|---|---|
| SP05-01 | parse_ui_scenario | parser | type="ui" parsed correctly | ✅ PASS |
| SP05-02 | parse_api_default | parser | No type → default "api" | ✅ PASS |
| SP05-03 | run_ui_scenario | orchestrator | BrowserEngine + ActionExecutor | ✅ PASS |
| SP05-04 | load_mixed_yaml | parser | Both types in one file | ✅ PASS |

## 2. Unit Tests — DB Verification (5 tests)

| # | Test Case | Module | Expected | Result |
|---|---|---|---|---|
| SP05-05 | db_verify_parse | parser | db_verify config parsed | ✅ PASS |
| SP05-06 | parse_no_db_verify | parser | No db_verify → None | ✅ PASS |
| SP05-07 | sqlite_adapter | db_tools | SELECT runs correctly | ✅ PASS |
| SP05-08 | db_adapter_none | db_tools | NoneAdapter returns True | ✅ PASS |
| SP05-09 | unknown_adapter | db_tools | Unknown → raises error | ✅ PASS |

## 3. Unit Tests — Version Auto-Detect (7 tests)

| # | Test Case | Module | Expected | Result |
|---|---|---|---|---|
| SP05-10 | detect_from_git_repo | version_detector | Returns SHA + tag | ✅ PASS |
| SP05-11 | detect_non_git_dir | version_detector | Returns "unknown" | ✅ PASS |
| SP05-12 | detect_none_dir | version_detector | Returns "unknown" | ✅ PASS |
| SP05-13 | version_in_db_save | results_db | Columns stored correctly | ✅ PASS |
| SP05-14 | version_in_db_get | results_db | Retrieved from run | ✅ PASS |
| SP05-15 | project_config_dir | config | project_dir field parsed | ✅ PASS |
| SP05-16 | version_default_unknown | results_db | Default = "unknown" | ✅ PASS |
