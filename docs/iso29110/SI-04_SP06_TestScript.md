# SI-04: Test Script — Sprint 06
# ⚖️ Forseti — Sprint 06 TDD Test Cases

| รายการ | รายละเอียด |
|---|---|
| **เอกสาร** | SI-04-SP06 |
| **Sprint** | Sprint 06 — Version Policy + LLM Feedback Agent |
| **วันที่** | 2026-03-18 |
| **จำนวน Test Cases** | 17 (unit) |
| **ผลการทดสอบ** | ✅ 111/111 total pass |

---

## 1. Unit Tests — SemVer Parser (3 tests)

| # | Test Case | Module | Expected | Result |
|---|---|---|---|---|
| SP06-01 | parse_standard_tag | version_detector | "v2.1.3" → (2,1,3) | ✅ PASS |
| SP06-02 | parse_no_v_prefix | version_detector | "1.0.0" → (1,0,0) | ✅ PASS |
| SP06-03 | parse_invalid | version_detector | "latest" → (0,0,0) | ✅ PASS |

## 2. Unit Tests — Version Suggestion (3 tests)

| # | Test Case | Module | Expected | Result |
|---|---|---|---|---|
| SP06-04 | suggest_from_repo | version_detector | Returns valid suggestion | ✅ PASS |
| SP06-05 | suggest_none_dir | version_detector | suggested = "v0.1.0" | ✅ PASS |
| SP06-06 | suggest_non_git_dir | version_detector | current = "none" | ✅ PASS |

## 3. Unit Tests — Version Tag (1 test)

| # | Test Case | Module | Expected | Result |
|---|---|---|---|---|
| SP06-07 | tag_non_git_dir | version_detector | success = False | ✅ PASS |

## 4. Unit Tests — FeedbackAgent Structure (6 tests)

| # | Test Case | Module | Expected | Result |
|---|---|---|---|---|
| SP06-08 | agent_init | feedback_agent | Model + api_key set | ✅ PASS |
| SP06-09 | format_scenarios | feedback_agent | Readable text output | ✅ PASS |
| SP06-10 | parse_valid_json | feedback_agent | JSON array parsed | ✅ PASS |
| SP06-11 | parse_code_block | feedback_agent | Markdown fenced → JSON | ✅ PASS |
| SP06-12 | parse_invalid_json | feedback_agent | Fallback item returned | ✅ PASS |
| SP06-13 | detect_test_types | feedback_agent | "api, ui" detected | ✅ PASS |

## 5. Unit Tests — FeedbackAgent Analysis (1 test)

| # | Test Case | Module | Expected | Result |
|---|---|---|---|---|
| SP06-14 | analyze_mocked | feedback_agent | Both backend + ui returned | ✅ PASS |

## 6. Unit Tests — Feedback Report (1 test)

| # | Test Case | Module | Expected | Result |
|---|---|---|---|---|
| SP06-15 | generate_report | feedback_agent | Markdown file created | ✅ PASS |

## 7. Unit Tests — Feedback DB (2 tests)

| # | Test Case | Module | Expected | Result |
|---|---|---|---|---|
| SP06-16 | save_and_get_feedback | results_db | Round-trip 2 items | ✅ PASS |
| SP06-17 | get_feedback_empty | results_db | Empty list for missing run | ✅ PASS |
