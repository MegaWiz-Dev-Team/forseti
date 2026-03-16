# SI-04: Test Scripts — Sprint 01
# ⚖️ Forseti — แนวทางการทดสอบตามมาตรฐาน ISO 29110

| รายการ | รายละเอียด |
|---|---|
| **เอกสาร** | SI-04-SP01 |
| **Sprint** | Sprint 01 — Foundation |
| **แนวทาง** | TDD (Test-Driven Development) |
| **วันที่** | 2026-03-16 |

---

## 1. TDD Process ที่ใช้

```
Red → Green → Refactor
 ↓       ↓        ↓
เขียน  implement  ปรับปรุง
test    code      code
ก่อน   ให้ test   โดย test
       ผ่าน      ยังผ่าน
```

## 2. Unit Test Scenarios

### 2.1 Data Models (`test_models.py`)

| TC ID | Test Case | Expected | Status |
|---|---|---|---|
| TC_SP01_U01 | สร้าง TestStep ด้วย action ภาษาไทย | action = "กรอก username ว่า admin", screenshot = True | ✅ Pass |
| TC_SP01_U02 | สร้าง TestStep แบบ no screenshot | screenshot = False | ✅ Pass |
| TC_SP01_U03 | สร้าง TestScenario ครบทุก field | name, steps, expected ถูกต้อง | ✅ Pass |
| TC_SP01_U04 | TestScenario with tags | tags = ["smoke", "login"] | ✅ Pass |
| TC_SP01_U05 | สร้าง TestScript | default phase = SIT | ✅ Pass |
| TC_SP01_U06 | TestScript ทุก phase | SIT, UAT, REGRESSION | ✅ Pass |
| TC_SP01_U07 | BrowserAction navigate | type = "navigate", selector = None | ✅ Pass |
| TC_SP01_U08 | BrowserAction click | type = "click", selector set | ✅ Pass |
| TC_SP01_U09 | TestSuiteResult all pass | pass_rate = 100% | ✅ Pass |
| TC_SP01_U10 | TestSuiteResult mixed | pass_rate ≈ 33.3% | ✅ Pass |
| TC_SP01_U11 | TestSuiteResult empty | pass_rate = 0% | ✅ Pass |

### 2.2 YAML Parser (`test_parser.py`)

| TC ID | Test Case | Expected | Status |
|---|---|---|---|
| TC_SP01_U12 | Parse valid YAML script | TestScript with correct fields | ✅ Pass |
| TC_SP01_U13 | Parse shorthand step syntax | String → TestStep | ✅ Pass |
| TC_SP01_U14 | Parse non-existent file | FileNotFoundError | ✅ Pass |
| TC_SP01_U15 | Parse invalid format (not a mapping) | ValueError | ✅ Pass |
| TC_SP01_U16 | Validate valid script | No issues | ✅ Pass |
| TC_SP01_U17 | Validate missing base_url | Issue reported | ✅ Pass |
| TC_SP01_U18 | Validate empty scenarios | Issue reported | ✅ Pass |
| TC_SP01_U19 | Validate missing expected | Issue reported | ✅ Pass |

### 2.3 Configuration (`test_config.py`)

| TC ID | Test Case | Expected | Status |
|---|---|---|---|
| TC_SP01_U20 | LLMConfig defaults | provider = "gemini", model = "gemini-2.0-flash" | ✅ Pass |
| TC_SP01_U21 | LLMConfig custom | provider = "ollama" | ✅ Pass |
| TC_SP01_U22 | BrowserConfig defaults | headless = True | ✅ Pass |
| TC_SP01_U23 | BrowserConfig headed | headless = False | ✅ Pass |
| TC_SP01_U24 | GitHubConfig defaults | enabled = False | ✅ Pass |
| TC_SP01_U25 | GitHubConfig enabled | enabled = True | ✅ Pass |
| TC_SP01_U26 | from_env — GEMINI_API_KEY | api_key loaded | ✅ Pass |
| TC_SP01_U27 | from_env — GITHUB_TOKEN + REPO | github.enabled = True | ✅ Pass |
| TC_SP01_U28 | from_env — custom LLM provider | provider = "ollama" | ✅ Pass |

### 2.4 Result Collector (`test_collector.py`)

| TC ID | Test Case | Expected | Status |
|---|---|---|---|
| TC_SP01_U29 | Save + load JSON | Round-trip preserves data | ✅ Pass |
| TC_SP01_U30 | Get summary stats | pass_rate = 50% | ✅ Pass |
| TC_SP01_U31 | Auto-generated filename | Contains "forseti_SIT_" | ✅ Pass |

## 3. สรุปผลการทดสอบ

| Metric | ค่า |
|---|---|
| **Total Test Cases** | 34 |
| **Passed** | 34 |
| **Failed** | 0 |
| **Pass Rate** | 100% ✅ |
| **Test Duration** | 1.49s |

## 4. Test Execution Command

```bash
cd /Users/paripolt/Projects/MyHero/forseti
source .venv/bin/activate
python -m pytest tests/ -v
```

## 5. Verification Checklist

- [x] All unit tests pass (34/34)
- [x] No test warnings that affect functionality
- [x] Test coverage covers core modules: models, parser, config, collector
- [x] TDD approach followed: tests written alongside implementation
- [ ] Integration tests with real LLM (Sprint 02)
- [ ] E2E test against real website (Sprint 02)
