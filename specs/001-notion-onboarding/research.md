# Research: Notion 帳號 Onboarding 優化

**Date**: 2026-03-30

## R1: Sidebar 渲染順序與 Streamlit 生命週期

**Decision**: 將 `_show_notion_accounts()` 和 `_show_style_settings()` 移到 `_check_config()` 之前呼叫

**Rationale**: Streamlit 的渲染是順序執行的。如果 `_check_config()` 在前面 `return`，後面的所有 `st.*` 呼叫都不會執行。把 sidebar 渲染放前面，確保無論 config 是否通過，sidebar 都能顯示。

**Alternatives considered**:
- 把 sidebar 放在 `_check_config()` 裡面的 else 分支 → 邏輯太耦合，sidebar 和 config check 不相關
- 用 `st.sidebar` context manager 包整個 main → 會讓程式結構混亂

## R2: Config Check 分層策略

**Decision**: `_check_config()` 只阻擋 OPENAI_API_KEY 缺失；Notion token 缺失改用獨立檢查且不阻擋 sidebar

**Rationale**: OPENAI_API_KEY 是所有核心功能（轉錄 + 摘要）的前提，缺失無法使用任何功能。Notion token 則只影響上傳步驟，且可以在 UI 動態新增，不應阻擋整個 app。

**Alternatives considered**:
- 維持原本合併檢查但改提示文字 → 仍然會 return，sidebar 不會顯示
- 完全移除 config check → OPENAI_API_KEY 缺失也不擋，使用者會在轉錄時才遇到更難懂的 API 錯誤

## R3: Expander 展開控制

**Decision**: `st.expander("🔑 Notion 帳號", expanded=not tokens)` — 有 token 時收合，無 token 時展開

**Rationale**: 新使用者首次使用時，最重要的操作就是新增 token。自動展開 expander 降低操作門檻，不需要使用者自己找到展開按鈕。有 token 後收合避免佔用過多側邊欄空間。

**Alternatives considered**:
- 永遠展開 → 有 token 後沒必要，浪費空間
- 用 popover/modal 替代 → Streamlit 不原生支援 modal，增加不必要的複雜度

## R4: Page Selector Guard

**Decision**: `_show_notion_page_selector()` 開頭加 `if not st.session_state.get("active_notion_token")` guard

**Rationale**: 無 active token 時呼叫 `search_pages()` 會發出帶空 Bearer token 的 API request，導致 401 錯誤。加 guard 直接顯示提示訊息更友善。

**Alternatives considered**:
- 在 `search_pages()` 內部檢查 → 可以，但錯誤訊息（HTTP 401）對使用者不友善
- 讓 `_show_notion_page_selector()` 不被呼叫 → 需要在多個呼叫點加條件，不如在函數內部一處處理
