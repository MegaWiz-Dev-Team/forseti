# PM-01: Project Plan
# ⚖️ Forseti — แผนบริหารโครงการตามมาตรฐาน ISO 29110

| รายการ | รายละเอียด |
|---|---|
| **เอกสาร** | PM-01 (Project Plan) |
| **โครงการ** | Forseti — LLM-Powered E2E Testing Service |
| **มาตรฐาน** | ISO/IEC 29110 Part 5-1-2 (Basic Profile) |
| **Methodology** | Agile (Scrum) + TDD |
| **วันที่** | 2026-03-16 |

---

## 1. ภาพรวมโครงการ

### 1.1 วัตถุประสงค์
พัฒนา self-hosted E2E testing service ที่ใช้ LLM แปลง natural language test script เป็น browser action เพื่อทดสอบ web application แบบอัตโนมัติ

### 1.2 ขอบเขตผลิตภัณฑ์
อ้างอิงตาม BRD-01 Section 3

### 1.3 เอกสารอ้างอิง
| เอกสาร | คำอธิบาย |
|---|---|
| BRD-01 | Business Requirements Document |
| TRD-01 | Technical Requirements Document |
| SI-01 | Software Requirements Specification |
| SI-03 | Traceability Matrix |
| SI-04 | Test Scripts |

## 2. Sprint Planning (Agile)

### Sprint 1 — Foundation (Week 1)
| # | User Story | Story Points | Status |
|---|---|---|---|
| US-01 | เขียน test script เป็น YAML ภาษาไทย/อังกฤษได้ | 3 | ✅ Done |
| US-02 | ระบบแปลง NL step เป็น browser action ผ่าน Gemini | 8 | ✅ Done |
| US-03 | ระบบรัน test ผ่าน Playwright browser ได้ | 5 | ✅ Done |
| US-04 | ระบบตรวจ expected result ผ่าน LLM assertion | 5 | ✅ Done |
| US-05 | บันทึกผลเป็น JSON + HTML report | 5 | ✅ Done |
| US-06 | เปิด GitHub issue อัตโนมัติเมื่อ test fail | 3 | ✅ Done |
| US-07 | CLI: `forseti run`, `validate`, `report`, `info` | 3 | ✅ Done |

### Sprint 2 — Enhancement (Planned)
| # | User Story | Story Points | Status |
|---|---|---|---|
| US-08 | Web dashboard แสดงผล real-time | 8 | 📋 Planned |
| US-09 | Historical trend tracking | 5 | 📋 Planned |
| US-10 | CI/CD pipeline integration (GitHub Actions) | 3 | 📋 Planned |
| US-11 | Parallel scenario execution | 5 | 📋 Planned |

## 3. ทีมงาน

| บทบาท | ความรับผิดชอบ |
|---|---|
| Product Owner | กำหนด requirements, prioritize backlog |
| Developer | พัฒนาระบบตาม TDD |
| QA | เขียน test scripts, ตรวจสอบผลการทดสอบ |

## 4. เครื่องมือการจัดการ

| เครื่องมือ | วัตถุประสงค์ |
|---|---|
| GitHub | Repository + Issue Tracking |
| GitHub Actions | CI/CD (planned) |
| pytest | Unit Testing (TDD) |
| Ruff | Code Quality |

## 5. ความเสี่ยง

| # | ความเสี่ยง | ผลกระทบ | แผนรับมือ |
|---|---|---|---|
| R-01 | LLM ตีความ NL ผิด → action ไม่ตรง | สูง | ปรับ prompt engineering, เพิ่ม fallback |
| R-02 | Website เปลี่ยน UI → test fail | กลาง | LLM-based selector healing |
| R-03 | Gemini API downtime | กลาง | Fallback to self-hosted LLM |
| R-04 | Rate limiting จาก LLM API | ต่ำ | Implement retry + backoff |
