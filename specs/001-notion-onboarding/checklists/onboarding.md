# Onboarding Requirements Quality Checklist: Notion 帳號 Onboarding 優化

**Purpose**: 驗證 spec/plan/tasks 三份文件的需求品質 — 完整性、清晰度、一致性、可量測性、情境覆蓋
**Created**: 2026-03-30
**Feature**: [spec.md](../spec.md) | [plan.md](../plan.md) | [tasks.md](../tasks.md)
**Focus**: 全面需求品質（UX Onboarding + 防禦性設計）
**Depth**: 標準（PR 審查級別）

## Requirement Completeness

- [x] CHK001 - Are sidebar visibility requirements defined for ALL config failure states (no OPENAI_API_KEY, no Notion token, both missing)? [Completeness, Spec §FR-002]
- [x] CHK002 - Are the exact UI elements that must remain visible during config failure enumerated? [Completeness, Spec §FR-002]
- [x] CHK003 - Is the rendering order between sidebar and config check explicitly documented as a requirement, not just an implementation detail? [Completeness, Gap]
- [x] CHK004 - Are requirements defined for what happens when a user removes ALL tokens after previously having some? [Completeness, Spec §Edge Cases]
- [x] CHK005 - Is the token validation timing explicitly specified (startup vs. first API call)? [Completeness, Spec §Assumptions]
- [x] CHK006 - Are requirements for the "meeting browser" sidebar section defined in the no-token state? [Completeness, Gap]

## Requirement Clarity

- [x] CHK007 - Is "主流程功能" quantified — which specific features are blocked vs. available without Notion token? [Clarity, Spec §FR-003]
- [x] CHK008 - Is "完整的 app 介面" in SC-001 defined with specific UI elements that must be present? [Clarity, Spec §SC-001]
- [x] CHK009 - Is the引導提示 text content specified as a firm requirement or merely a suggestion? [Clarity, Spec §US2-AS1]
- [x] CHK010 - Is "10 秒內" in SC-001 measurable under defined conditions (cold start vs. warm, machine specs)? [Measurability, Spec §SC-001]
- [x] CHK011 - Is "2 分鐘內" in SC-002 scoped to specific user actions, excluding external factors (Notion signup, API latency)? [Measurability, Spec §SC-002]

## Requirement Consistency

- [x] CHK012 - Do FR-001 and FR-003 have consistent definitions of "阻擋" (FR-001 says Notion token doesn't block; FR-003 says no-token blocks main flow)? [Consistency, Spec §FR-001, §FR-003]
- [x] CHK013 - Are the引導提示 text strings consistent between spec (US2-AS1) and tasks (T003)? [Consistency, Spec §US2 vs Tasks §T003]
- [x] CHK014 - Is the term "active Notion token" used consistently across spec (US3), plan, and tasks? [Consistency, Spec §US3, §FR-005, §Key Entities]
- [x] CHK015 - Does the plan's Constitution Check align with the spec's Assumptions section? [Consistency, Plan §Constitution Check vs Spec §Assumptions]

## Acceptance Criteria Quality

- [x] CHK016 - Can SC-003 ("100% 的無 token 啟動情境下") be objectively verified without exhaustive testing? [Measurability, Spec §SC-003]
- [x] CHK017 - Are acceptance scenarios for US1 sufficient to verify the "解鎖" transition from blocked to unblocked? [Acceptance Criteria, Spec §US1-AS3]
- [x] CHK018 - Does US4 define acceptance criteria for what error message content must include? [Acceptance Criteria, Spec §US4-AS1]
- [x] CHK019 - Are acceptance criteria for the expander auto-expand (FR-004) testable — how to verify expanded state programmatically? [Acceptance Criteria, Spec §FR-004]

## Scenario Coverage

- [x] CHK020 - Are requirements defined for the "有 token → 刪除全部 → 無 token" state transition flow? [Coverage, Spec §Edge Cases]
- [x] CHK021 - Are requirements defined for multiple concurrent browser tabs accessing the same app? [Coverage, Gap]
- [x] CHK022 - Are error recovery requirements specified when .notion_tokens.json is corrupted mid-operation? [Coverage, Spec §Edge Cases]
- [x] CHK023 - Is the behavior specified when Notion API returns 401 (invalid/expired token) during page selector? [Coverage, Gap]
- [x] CHK024 - Are requirements defined for the order of config check errors when BOTH OPENAI_API_KEY and Notion token are missing? [Coverage, Spec §Edge Cases]

## Edge Case Coverage

- [x] CHK025 - Is the fallback behavior specified when .notion_tokens.json has valid JSON but unexpected schema? [Edge Case, Spec §Edge Cases]
- [x] CHK026 - Are requirements defined for token label uniqueness or duplicate handling? [Edge Case, Gap]
- [x] CHK027 - Is the empty string token case handled (user submits blank token)? [Edge Case, Gap]
- [x] CHK028 - Is the behavior defined when .env has NOTION_TOKEN and .notion_tokens.json also has the same token? [Edge Case, Spec §FR-007]

## Non-Functional Requirements

- [x] CHK029 - Are performance requirements for config check defined beyond the vague "10 秒" in SC-001? [NFR, Spec §SC-001]
- [x] CHK030 - Are security requirements specified for token storage (file permissions, encryption at rest)? [NFR, Gap]
- [x] CHK031 - Is the accessibility of the引導提示 and expander auto-expand addressed for screen readers? [NFR, Gap]

## Dependencies & Assumptions

- [x] CHK032 - Is the assumption "現有的 token 讀取與儲存機制維持不變" validated against actual code? [Assumption, Spec §Assumptions]
- [x] CHK033 - Is the dependency on Streamlit's `st.rerun()` for FR-006 explicitly documented as a technical constraint? [Dependency, Tasks §Phase 6 Notes]
- [x] CHK034 - Is the dependency on `config.load_notion_tokens()` behavior documented in the spec rather than only in tasks? [Dependency, Gap]

## Ambiguities & Conflicts

- [x] CHK035 - Does "config check 未通過" in FR-002 include both OPENAI_API_KEY failure AND Notion token absence, or only the former? [Ambiguity, Spec §FR-002]

## Notes

- 本 checklist 測試**需求文件本身的品質**，而非實作是否正確
- 標記 `[Gap]` 的項目表示 spec 中可能需要補充的缺失需求
- 標記 `[Ambiguity]` 的項目表示現有描述可能有多種解讀
- 共 35 項，按品質維度分組

### [Gap] Resolution Notes

| CHK | Gap | 處置 |
|-----|-----|------|
| CHK006 | Meeting browser 在 no-token 狀態 | 已新增 FR-008 + US1-AS4 覆蓋 |
| CHK021 | 多 tab 併發 | 不在 scope — 單人本地工具，Streamlit session 隔離 |
| CHK023 | 401 錯誤處理 | Edge Cases「無效 token → 後續 API 呼叫顯示錯誤」涵蓋 |
| CHK026 | Label 重複 | 不在 scope — label 僅為顯示用途，重複不影響功能 |
| CHK027 | 空 token 提交 | 代碼已有 `if new_label and new_token:` 防護 |
| CHK030 | Token 儲存安全 | 接受風險 — 本地檔案 + .gitignore 排除，足夠 |
| CHK031 | 可及性 (a11y) | 不在 scope — Streamlit 框架內建基本 a11y |
