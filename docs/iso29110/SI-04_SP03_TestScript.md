# SI-04: Test Script — Sprint 03
# ⚖️ Forseti — Sprint 03 TDD Test Cases

| รายการ | รายละเอียด |
|---|---|
| **เอกสาร** | SI-04-SP03 |
| **Sprint** | Sprint 03 — Reporter Agent + Orchestrator |
| **วันที่** | 2026-03-18 |
| **จำนวน Test Cases** | 10 (unit) + 26 (E2E) |
| **ผลการทดสอบ** | ✅ 71/71 unit pass, 26/26 E2E pass |

---

## 1. Unit Tests — ReporterAgent (6 tests)

| # | Test Case | Module | Expected | Result |
|---|---|---|---|---|
| SP03-01 | save_to_sqlite | reporter_agent | Run saved, scenarios saved | ✅ PASS |
| SP03-02 | generate_iso_report | reporter_agent | SI-04 markdown generated | ✅ PASS |
| SP03-03 | generate_summary | reporter_agent | Human-readable summary | ✅ PASS |
| SP03-04 | build_github_issue | reporter_agent | Title + body with failures | ✅ PASS |
| SP03-05 | no_issue_when_all_pass | reporter_agent | Returns None | ✅ PASS |
| SP03-06 | full_report_pipeline | reporter_agent | DB + ISO + summary | ✅ PASS |

## 2. Unit Tests — ForsetiOrchestrator (4 tests)

| # | Test Case | Module | Expected | Result |
|---|---|---|---|---|
| SP03-07 | create_orchestrator | orchestrator | Config stored | ✅ PASS |
| SP03-08 | build_api_scenarios | orchestrator | ≥20 scenarios from YAML | ✅ PASS |
| SP03-09 | run_single_scenario_mock | orchestrator | Pass/fail returned | ✅ PASS |
| SP03-10 | report_generated_after_run | orchestrator | Run saved in DB | ✅ PASS |

## 3. E2E Integration Tests — Live Server (26 scenarios)

| # | Test Case | Endpoint | Expected | Result |
|---|---|---|---|---|
| TC_E2E_01 | Email Check (Existing) | POST /api/student/check-email | 200 | ✅ |
| TC_E2E_02 | Email Check (Not Found) | POST /api/student/check-email | 404 | ✅ |
| TC_E2E_07 | Get Student Profile | GET /api/student/{email}/profile | 200 | ✅ |
| TC_E2E_08 | Update Profile Phone | POST /api/student/update-profile | 200 | ✅ |
| TC_E2E_09 | Accept PDPA Consent | POST /api/student/consent | 200 | ✅ |
| TC_E2E_11 | Save DISC Result | POST /api/student/disc | 200 | ✅ |
| TC_E2E_12 | Invalid DISC Type | POST /api/student/disc | 400 | ✅ |
| TC_E2E_13 | Load Quiz Config | GET /api/quiz/{batch}/pretest | 200 | ✅ |
| TC_E2E_21 | Attendance Report | GET /api/admin/batch/{id}/attendance | 200 | ✅ |
| TC_E2E_38 | Submit Feedback | POST /api/student/feedback | 200 | ✅ |
| TC_E2E_39 | Feedback Report | GET /api/admin/batch/{id}/feedback | 200 | ✅ |
| TC_E2E_42 | List Batches | GET /api/admin/batches | 200 | ✅ |
| TC_E2E_43 | Get Batch Detail | GET /api/admin/batch/{id} | 200 | ✅ |
| TC_E2E_44 | Batch Not Found | GET /api/admin/batch/NONEXISTENT | 404 | ✅ |
| TC_E2E_45 | List Programs | GET /api/programs | 200 | ✅ |
| TC_E2E_46 | Update emailConfig | PUT /api/programs/{id} | 200 | ✅ |
| TC_E2E_47 | Get Materials | GET /api/programs/{id}/materials | 200 | ✅ |
| TC_E2E_28 | Invitation Dry Run | POST admin/batch/{id}/send-invitations | 200 | ✅ |
| TC_E2E_30 | Reminder Dry Run | POST admin/batch/{id}/send-reminders | 200 | ✅ |
| TC_E2E_32 | Score Announce Dry Run | POST admin/batch/{id}/announce-scores | 200 | ✅ |
| TC_E2E_34 | Certificate Dry Run | POST admin/batch/{id}/send-certificates | 200 | ✅ |
| TC_E2E_36 | Reset Email Status | POST admin/batch/{id}/reset-email | 200 | ✅ |
| TC_E2E_26 | Manual Grade | POST /api/admin/grade | 200 | ✅ |
| TC_E2E_49 | Public Registration | POST /api/public/register | 200 | ✅ |
| TC_E2E_50 | Unauthorized Access | GET /api/admin/batches (no auth) | 401 | ✅ |
| TC_E2E_52 | Invalid Batch (No Auth) | GET /api/admin/batch/X (no auth) | 401 | ✅ |

## 4. E2E Run History (SQLite)

| Run | Pass Rate | Duration | Key Change |
|:---:|:---------:|:--------:|------------|
| #1 | 15% | 1.0s | First run |
| #2 | 35% | 1.2s | Fixed YAML body parsing |
| #3 | 35% | 0.7s | OTP dev mode |
| #4 | 81% | 4.7s | Admin password fixed |
| **#5** | **100%** | **9.4s** | **All 5 fixes applied** |
