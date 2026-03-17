# SI-04: Test Script — Sprint 02
# ⚖️ Forseti — ADK Multi-Agent + API Test Runner

| รายการ | รายละเอียด |
|---|---|
| **เอกสาร** | SI-04-SP02 |
| **Sprint** | Sprint 02 — ADK Multi-Agent + API Test Runner |
| **Methodology** | TDD (Red → Green → Refactor) |
| **Model** | gemini-3.1-flash-lite-preview |
| **Target** | cloud-super-hero-dev (ห้าม production) |

---

## TDD Test Matrix

### Module 1: API HTTP Tools (`tools/http_tools.py`)

| TC ID | Test Case | Input | Expected | Status |
|---|---|---|---|---|
| TC_SP02_01 | http_get returns status + body | GET /health | `{status: 200, body: ...}` | 📋 |
| TC_SP02_02 | http_post sends JSON body | POST /api/student/check-email | `{status: 200, ...}` | 📋 |
| TC_SP02_03 | http_put sends update | PUT /api/programs/dev | `{status: 200, ...}` | 📋 |
| TC_SP02_04 | http_get with auth header | GET /api/admin/batches + Bearer | `{status: 200, list}` | 📋 |
| TC_SP02_05 | http_get no auth returns 401 | GET /api/admin/batches | `{status: 401}` | 📋 |

### Module 2: Assert Tools (`tools/assert_tools.py`)

| TC ID | Test Case | Input | Expected | Status |
|---|---|---|---|---|
| TC_SP02_06 | assert_status pass | response(200), expected=200 | `{passed: true}` | 📋 |
| TC_SP02_07 | assert_status fail | response(404), expected=200 | `{passed: false}` | 📋 |
| TC_SP02_08 | assert_json_field pass | body=`{"ok":true}`, path="ok" | `{passed: true}` | 📋 |
| TC_SP02_09 | assert_json_field nested | body=`{"data":{"id":1}}`, path="data.id" | `{passed: true, value: 1}` | 📋 |
| TC_SP02_10 | assert_json_field missing | body=`{}`, path="name" | `{passed: false}` | 📋 |

### Module 3: Auth Tools (`tools/auth_tools.py`)

| TC ID | Test Case | Input | Expected | Status |
|---|---|---|---|---|
| TC_SP02_11 | admin_login success | email + password | `{token: "..."}` | 📋 |
| TC_SP02_12 | admin_login wrong password | bad password | `{error: "..."}` | 📋 |
| TC_SP02_13 | get_auth_headers returns Bearer | token="abc" | `{"Authorization": "Bearer abc"}` | 📋 |

### Module 4: API Agent Models (`agents/api_agent.py`)

| TC ID | Test Case | Input | Expected | Status |
|---|---|---|---|---|
| TC_SP02_14 | ApiTestAgent has correct tools | — | 7 tools registered | 📋 |
| TC_SP02_15 | ApiTestAgent model is correct | — | gemini-3.1-flash-lite-preview | 📋 |
| TC_SP02_16 | ApiTestAgent instruction is set | — | Non-empty instruction | 📋 |

### Module 5: ISO Report Generator (`reporter/iso_report.py`)

| TC ID | Test Case | Input | Expected | Status |
|---|---|---|---|---|
| TC_SP02_17 | generate_iso_report produces markdown | TestSuiteResult | Valid `.md` string | 📋 |
| TC_SP02_18 | report has correct header table | result | Contains SI-04 metadata | 📋 |
| TC_SP02_19 | report has test matrix | result with 5 scenarios | 5-row table | 📋 |
| TC_SP02_20 | report has pass/fail summary | 4 pass + 1 fail | pass_rate = 80% | 📋 |
| TC_SP02_21 | report saves to file | result + path | File exists on disk | 📋 |

### Module 6: YAML Test Script (`examples/cloud_super_hero_e2e.yaml`)

| TC ID | Test Case | Input | Expected | Status |
|---|---|---|---|---|
| TC_SP02_22 | YAML parses without error | load + parse | Valid TestScript | 📋 |
| TC_SP02_23 | Has ≥ 10 API scenarios | parsed.scenarios | len ≥ 10 | 📋 |
| TC_SP02_24 | All scenarios have expected | parsed | all expected non-empty | 📋 |
| TC_SP02_25 | Base URL is dev server | parsed.base_url | localhost:8080 | 📋 |

### Module 7: Integration Test

| TC ID | Test Case | Input | Expected | Status |
|---|---|---|---|---|
| TC_SP02_26 | Full API test run (dry) | YAML script | TestSuiteResult with all SKIP | 📋 |
| TC_SP02_27 | Save result as JSON | run result | JSON file in results/ | 📋 |
| TC_SP02_28 | Save result as ISO report | run result | MD file in reports/ | 📋 |

---

## Test Summary

| Module | # Tests | ลำดับ TDD |
|---|---|---|
| HTTP Tools | 5 | 🔴 Red → 🟢 Green first |
| Assert Tools | 5 | 🔴 Red → 🟢 Green |
| Auth Tools | 3 | 🔴 Red → 🟢 Green |
| API Agent | 3 | After tools done |
| ISO Reporter | 5 | 🔴 Red → 🟢 Green |
| YAML Script | 4 | After agent done |
| Integration | 3 | Last (🟢 final verify) |
| **Total** | **28** | |

## TDD Execution Order

```
1. [Red]   เขียน test_http_tools.py     → 5 tests FAIL
2. [Green] implement http_tools.py       → 5 tests PASS
3. [Red]   เขียน test_assert_tools.py   → 5 tests FAIL
4. [Green] implement assert_tools.py     → 5 tests PASS
5. [Red]   เขียน test_auth_tools.py     → 3 tests FAIL
6. [Green] implement auth_tools.py       → 3 tests PASS
7. [Red]   เขียน test_api_agent.py       → 3 tests FAIL
8. [Green] implement api_agent.py        → 3 tests PASS (ADK Agent)
9. [Red]   เขียน test_iso_report.py      → 5 tests FAIL
10.[Green] implement iso_report.py       → 5 tests PASS
11.[Red]   เขียน test_yaml_script.py     → 4 tests FAIL
12.[Green] create YAML test script       → 4 tests PASS
13.[Green] integration test              → 3 tests PASS
14.[Refactor] Clean up + doc             → All 28 PASS ✅
```
