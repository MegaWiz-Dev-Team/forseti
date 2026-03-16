# BRD-01: Business Requirements Document
# ⚖️ Forseti — LLM-Powered E2E Testing Service

| รายการ | รายละเอียด |
|---|---|
| **เอกสาร** | BRD-01 |
| **โครงการ** | Forseti (ฟอร์เซตี) |
| **เวอร์ชัน** | 1.0 |
| **วันที่** | 2026-03-16 |
| **ผู้จัดทำ** | MyHero Team |
| **สถานะ** | Draft |

---

## 1. บทสรุปผู้บริหาร (Executive Summary)

**Forseti** เป็น self-hosted E2E testing service ที่ใช้ LLM (Large Language Model) ในการแปลง natural language test script เป็น browser action เพื่อทดสอบระบบ web application แบบอัตโนมัติ สามารถบันทึกผล ออกรายงาน และเชื่อมต่อกับ GitHub ได้

## 2. วัตถุประสงค์ทางธุรกิจ (Business Objectives)

| # | วัตถุประสงค์ | KPI |
|---|---|---|
| BO-1 | ลดเวลาการทดสอบ E2E จากการทำ manual | ลดเวลา ≥ 60% |
| BO-2 | ลดข้อผิดพลาดจากการทดสอบแบบ manual | ลด missing defects ≥ 50% |
| BO-3 | เพิ่มความสามารถในการ track ผลการทดสอบ SIT/UAT | 100% traceability |
| BO-4 | ลดเวลาในการแจ้ง defect กลับทีมพัฒนา | Auto-create issue < 1 นาที |

## 3. ขอบเขต (Scope)

### 3.1 In Scope
- อ่าน test script จาก YAML (รองรับภาษาไทยและอังกฤษ)
- ใช้ LLM (Gemini / Self-hosted) แปลง NL → browser action
- รัน test ผ่าน Playwright browser automation
- ตรวจสอบ expected result ผ่าน LLM assertion
- บันทึกผลเป็น JSON + สร้าง HTML report
- ติดตาม pass/fail rate เป็น %
- เปิด GitHub issue อัตโนมัติเมื่อ test fail
- รองรับ phase: SIT, UAT, REGRESSION
- CLI interface สำหรับ developer

### 3.2 Out of Scope (Phase 1)
- Web Dashboard UI
- API testing (non-browser)
- Mobile native app testing
- Performance/load testing
- Multi-user concurrent execution

## 4. Stakeholders

| Role | ความรับผิดชอบ |
|---|---|
| QA Team | เขียน test script, review ผลการทดสอบ |
| Dev Team | แก้ไข defect ตาม GitHub issues |
| Project Manager | ติดตาม % pass rate ใน SIT/UAT |
| DevOps | Deploy & maintain Forseti service |

## 5. Functional Requirements

| ID | Requirement | Priority | Phase |
|---|---|---|---|
| FR-01 | ระบบต้องอ่าน test script จาก YAML | Must | 1 |
| FR-02 | ระบบต้องใช้ LLM แปลง NL step → browser action | Must | 1 |
| FR-03 | ระบบต้อง execute actions ผ่าน Playwright | Must | 1 |
| FR-04 | ระบบต้องตรวจ expected result ผ่าน LLM assertion | Must | 1 |
| FR-05 | ระบบต้องบันทึกผลเป็น JSON | Must | 1 |
| FR-06 | ระบบต้องสร้าง HTML report + % pass rate | Must | 1 |
| FR-07 | ระบบต้องเปิด GitHub issue เมื่อ test fail | Must | 1 |
| FR-08 | ระบบต้องรองรับ dry-run mode | Should | 1 |
| FR-09 | ระบบต้อง capture screenshot ทุก step | Should | 1 |
| FR-10 | ระบบต้องรองรับ self-hosted LLM (OpenAI-compatible) | Should | 1 |
| FR-11 | ระบบต้องมี web dashboard แสดงผล real-time | Could | 2 |

## 6. Non-Functional Requirements

| ID | Requirement | เกณฑ์ |
|---|---|---|
| NFR-01 | ต้อง self-hosted ได้ทั้งหมด | ไม่มี SaaS dependency |
| NFR-02 | รองรับ Python 3.11+ | ใช้ modern Python features |
| NFR-03 | ต้องรองรับ headless browser | สำหรับ CI/CD pipeline |
| NFR-04 | ต้องรองรับ Gemini API | Gemini 2.0 Flash |
| NFR-05 | Report ต้อง bilingual (Thai/EN) | ตาม test script |

## 7. Acceptance Criteria

| # | เกณฑ์ | วิธีทดสอบ |
|---|---|---|
| AC-1 | สร้าง YAML test script ภาษาไทย → รัน → ได้ผล pass/fail | E2E test |
| AC-2 | ผล test fail → GitHub issue ถูกสร้างอัตโนมัติ | Integration test |
| AC-3 | HTML report มี % pass rate, screenshot ทุก step | Visual inspection |
| AC-4 | dry-run mode แสดง action plan โดยไม่เปิด browser | Unit test |
| AC-5 | Unit test coverage ≥ 80% | pytest --cov |
