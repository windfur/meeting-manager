import re
import json
import streamlit as st
from pathlib import Path
from datetime import date, datetime
import config


st.set_page_config(page_title="會議管理助手", page_icon="🎙️", layout="wide")


def main():
    st.title("🎙️ 會議管理助手")
    st.caption("上傳錄音 → 審閱逐字稿 → AI 摘要 → 審閱修改 → 存入 Notion")

    if not _check_config():
        return

    # 初始化 session state
    for key in ['raw_transcript', 'confirmed_transcript', 'summary',
                'summary_draft', 'key_points', 'output_dir', 'page_url',
                'step', 'meeting_name', 'date_str', 'tags', 'participants',
                'replace_pairs_count', 'editor_version', 'summarizing']:
        if key not in st.session_state:
            st.session_state[key] = None
    if st.session_state.step is None:
        st.session_state.step = 0
    if st.session_state.replace_pairs_count is None:
        st.session_state.replace_pairs_count = 1
    if st.session_state.editor_version is None:
        st.session_state.editor_version = 0
    if st.session_state.summarizing is None:
        st.session_state.summarizing = False

    # --- 輸入區 ---
    st.header("📁 上傳會議檔案")

    uploaded_file = st.file_uploader(
        "拖拉或選擇音檔 / 影音檔",
        type=['mp3', 'mp4', 'wav', 'm4a', 'ogg', 'webm', 'mpeg', 'mpga'],
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        meeting_name = st.text_input("會議名稱 *", placeholder="例：週會、客戶訪談")
    with col2:
        meeting_date = st.date_input("會議日期 *", value=date.today())
    with col3:
        tags_input = st.text_input("標籤（逗號分隔）", placeholder="例：專案A, 進度追蹤")

    participants_input = st.text_input(
        "參與者（選填，逗號分隔）",
        placeholder="例：James, Frank, Justin, 宇航",
    )

    tags = [t.strip() for t in tags_input.split(',') if t.strip()] if tags_input else []
    participants = [p.strip() for p in participants_input.split(',') if p.strip()] if participants_input else []
    date_str = meeting_date.strftime('%Y-%m-%d')

    st.caption(f"🤖 摘要模型：`{config.LLM_MODEL}`（可在 .env 切換）")

    # --- Sidebar: 摘要偏好設定 ---
    _show_style_settings()

    # --- Step 1: 轉錄按鈕 ---
    can_start = uploaded_file is not None and bool(meeting_name)
    if st.button("🚀 開始轉錄", type="primary", disabled=not can_start):
        st.session_state.meeting_name = meeting_name
        st.session_state.date_str = date_str
        st.session_state.tags = tags
        st.session_state.participants = participants
        st.session_state.page_url = None
        # 重設後續步驟
        for key in ['confirmed_transcript', 'summary', 'summary_draft', 'key_points']:
            st.session_state[key] = None
        st.session_state.replace_pairs_count = 1
        _do_transcription(uploaded_file, meeting_name, date_str)

    # --- 根據步驟顯示對應畫面（if/elif 確保同一次 render 只畫一個 step）---
    if st.session_state.step == 1:
        _show_transcript_review()
    elif st.session_state.step == 2:
        _show_summary_review()

    # --- Step 3: 結果 ---
    _show_upload_result()


# ──────────────────────────────────────────────
# Config check
# ──────────────────────────────────────────────

def _check_config():
    issues = []
    if not config.OPENAI_API_KEY:
        issues.append("缺少 OPENAI_API_KEY")
    if not config.NOTION_TOKEN:
        issues.append("缺少 NOTION_TOKEN")
    if not config.NOTION_PARENT_PAGE_ID:
        issues.append("缺少 NOTION_PARENT_PAGE_ID")
    if issues:
        st.error("⚠️ 設定不完整，請編輯 `.env` 檔案：\n" + "\n".join(f"- {i}" for i in issues))
        return False
    return True


# ──────────────────────────────────────────────
# Sidebar: 摘要偏好設定
# ──────────────────────────────────────────────

def _show_style_settings():
    style_file = config.SUMMARY_STYLE_FILE

    # 結構化規範範本 — 使用者按一鍵就能得到骨架，照著改就好
    STYLE_TEMPLATE = """# 摘要規範

## 語言規則
- 用繁體中文撰寫
- 技術術語保留英文（API、MQTT、TTL 等）
- 標題可中英混用

## 領域知識
<!-- 寫下你的團隊背景、常見術語、人名對照等，AI 會參考 -->
- 我們是 [團隊名稱]，負責 [業務範圍]
- 常見縮寫：[例如 PM = Product Manager]

## 寫作原則
- 不要編造逐字稿中沒有的資訊
- 不要省略技術細節、數字、參數
- 被放棄的方案也要記錄（說明為什麼放棄）
- 寧可寫長一點也不要遺漏重要資訊
- 30 分鐘以上的會議通常有 4-10 個主題

## 結論標記準則
- ✅ 被採納：有明確拍板語句
- ❌ 被放棄：有明確否決或轉向
- ⏳ 待確認：需要等其他人/事才能決定

## 主題拆分
- 只要有獨立的討論脈絡（提出 → 回應 → 結論），就拆成獨立主題
- 背景說明獨立成段
- 寧可多拆不要少拆

## 輸出格式

### 會議紀錄：[一句話概括]

#### 一、背景與問題
簡要說明會議起因、核心問題。

#### 二、討論內容

**Case [編號]：[標題]**
- **情境描述：** ...
- **討論要點：**
  - 用多層次結構，不要全部攤平
  - **方案 A** — 說明
    - 優點
    - 疑慮
- **結論：** ✅ / ⏳ / ❌ + 具體說明

#### 三、會議總結

**✅ 已確認的決議 / Action Items：**
- [具體可執行的項目]

**⏳ 待確認項目：**
- [待誰確認、確認什麼]

**❌ 被否決 / 放棄的方案：**
- [方案名稱] — 原因
""".strip()

    with st.sidebar:
        st.header("⚙️ 摘要規範設定")
        st.caption("定義 AI 產生摘要的規範，下次產生摘要時自動套用。")

        # 讀取現有內容
        current = ""
        if style_file.exists():
            current = style_file.read_text(encoding='utf-8').strip()

        # 產生範本按鈕（只在編輯器為空時顯示）
        if not current:
            if st.button("📋 產生規範範本", use_container_width=True,
                         help="一鍵填入結構化範本，你只需要修改內容"):
                st.session_state['style_editor'] = STYLE_TEMPLATE
                st.rerun()

        edited = st.text_area(
            "摘要規範",
            value=current,
            height=350,
            placeholder="點擊上方「📋 產生規範範本」開始，\n或直接寫你的摘要規範。\n\n建議包含：語言規則、領域知識、寫作原則、\n結論標記準則、主題拆分、輸出格式。",
            key="style_editor",
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 儲存", use_container_width=True):
                style_file.write_text(edited, encoding='utf-8')
                st.toast("✅ 摘要規範已儲存！")
                st.rerun()
        with col2:
            if st.button("🗑️ 清除", use_container_width=True):
                if style_file.exists():
                    style_file.unlink()
                if 'style_editor' in st.session_state:
                    del st.session_state['style_editor']
                st.success("已清除！")
                st.rerun()

        if edited.strip():
            st.info("✅ 規範已啟用，下次產生摘要時會套用。")
        else:
            st.caption("目前使用預設摘要規範。")


# ──────────────────────────────────────────────
# Step 1: 轉錄（只做轉錄，不做摘要）
# ──────────────────────────────────────────────

def _do_transcription(uploaded_file, meeting_name, date_str):
    from transcriber import transcribe

    st.session_state.step = 0

    safe_name = re.sub(r'[<>:"/\\|?*]', '_', meeting_name)
    dir_name = f"{date_str}_{safe_name}"
    output_dir = config.OUTPUT_DIR / dir_name
    output_dir.mkdir(parents=True, exist_ok=True)
    st.session_state.output_dir = str(output_dir)

    raw_path = output_dir / "transcript_raw.txt"
    has_existing = raw_path.exists()

    status = st.status("轉錄中...", expanded=True)

    try:
        if has_existing:
            status.write("📂 偵測到同日期同標題已有逐字稿，跳過轉錄")
            raw_transcript = raw_path.read_text(encoding='utf-8')

            audio_ext = Path(uploaded_file.name).suffix
            audio_path = output_dir / f"{safe_name}{audio_ext}"
            if not audio_path.exists():
                with open(audio_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
        else:
            status.update(label="儲存音檔...")
            audio_ext = Path(uploaded_file.name).suffix
            audio_path = output_dir / f"{safe_name}{audio_ext}"
            with open(audio_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            file_size_mb = audio_path.stat().st_size / (1024 * 1024)
            status.write(f"✅ 音檔已儲存（{file_size_mb:.1f} MB）")

            status.update(label="語音轉錄中...")
            result = transcribe(
                str(audio_path),
                progress_callback=lambda msg: status.write(f"⏳ {msg}")
            )
            raw_transcript = result['raw_text']
            (output_dir / "transcript_raw.txt").write_text(raw_transcript, encoding='utf-8')

        st.session_state.raw_transcript = raw_transcript
        st.session_state.step = 1
        status.update(label="✅ 轉錄完成，請審閱逐字稿", state="complete")
        status.write(f"共 {len(raw_transcript):,} 字")

    except Exception as e:
        status.update(label="❌ 轉錄失敗", state="error")
        status.write(f"❌ {str(e)}")


# ──────────────────────────────────────────────
# Step 1.5: 審閱逐字稿 + 批次取代
# ──────────────────────────────────────────────

def _show_transcript_review():
    if st.session_state.step != 1:
        return

    st.divider()
    st.header("📄 審閱逐字稿")

    # 顯示上一次摘要失敗的錯誤訊息
    if 'summarize_error' in st.session_state:
        st.error(f"❌ 摘要產生失敗：{st.session_state.summarize_error}")
        del st.session_state['summarize_error']

    st.info("👇 請檢查轉錄結果。如有人名或術語辨識錯誤，可用下方「批次取代」一次修正，或直接在文字框中編輯。")

    # --- 批次取代區 ---
    with st.expander("🔄 批次取代（人名 / 術語修正）", expanded=True):
        st.caption("輸入要取代的文字，按「套用」一次全部替換。適合修正整篇重複出現的辨識錯誤。")

        count = st.session_state.replace_pairs_count

        pairs = []
        for i in range(count):
            c1, c2 = st.columns(2)
            with c1:
                old = st.text_input(f"原文 {i+1}", key=f"replace_old_{i}", placeholder="例：余航")
            with c2:
                new = st.text_input(f"替換為 {i+1}", key=f"replace_new_{i}", placeholder="例：宇航")
            if old and new:
                pairs.append((old, new))

        col_add, col_apply = st.columns([1, 1])
        with col_add:
            if st.button("➕ 新增一組", key="add_pair"):
                st.session_state.replace_pairs_count += 1
                st.rerun()
        with col_apply:
            if st.button("🔄 套用取代", key="apply_replace", disabled=len(pairs) == 0):
                # 從 text_area 讀取（可能 user 有手動編輯過）
                current = st.session_state.get("transcript_editor", st.session_state.raw_transcript)
                applied = []
                for old, new in pairs:
                    n = current.count(old)
                    if n > 0:
                        current = current.replace(old, new)
                        applied.append(f"「{old}」→「{new}」（{n} 處）")
                st.session_state.raw_transcript = current
                # 版號+1，強制 text_area 重建以顯示取代結果
                st.session_state.editor_version += 1
                if applied:
                    st.toast("已取代：" + "、".join(applied))
                else:
                    st.toast("沒有找到符合的文字")
                st.rerun()

    # --- 可編輯的逐字稿（key 帶版號，批次取代後版號+1 強制重建 widget）---
    editor_key = f"transcript_editor_v{st.session_state.editor_version}"
    edited_transcript = st.text_area(
        "逐字稿內容（可編輯）",
        value=st.session_state.raw_transcript,
        height=500,
        key=editor_key,
    )

    # --- 確認 ---
    has_summary = st.session_state.summary is not None
    is_busy = st.session_state.summarizing
    cols = st.columns([1, 1, 2]) if has_summary else st.columns([1, 3])
    with cols[0]:
        btn_label = "⏳ 摘要產生中..." if is_busy else "✅ 確認逐字稿，產生摘要"
        if st.button(btn_label, type="primary", disabled=is_busy):
            final_transcript = st.session_state.get(editor_key, edited_transcript)
            st.session_state.raw_transcript = final_transcript
            st.session_state.confirmed_transcript = final_transcript
            output_dir = Path(st.session_state.output_dir)
            (output_dir / "transcript_raw.txt").write_text(
                final_transcript, encoding='utf-8'
            )
            st.session_state.summarizing = True
            st.rerun()
    if has_summary:
        with cols[1]:
            if st.button("➡️ 前往審閱摘要", disabled=is_busy):
                final_transcript = st.session_state.get(editor_key, edited_transcript)
                st.session_state.raw_transcript = final_transcript
                st.session_state.confirmed_transcript = final_transcript
                output_dir = Path(st.session_state.output_dir)
                (output_dir / "transcript_raw.txt").write_text(
                    final_transcript, encoding='utf-8'
                )
                st.session_state.step = 2
                st.rerun()

    # 摘要產生中：按鈕已 disabled，在畫面底部才真正執行摘要
    if is_busy:
        _do_summarize()
        st.rerun()


# ──────────────────────────────────────────────
# Step 2: 產生摘要
# ──────────────────────────────────────────────

def _do_summarize():
    from summarizer import summarize

    status = st.status("產生摘要中...", expanded=True)

    try:
        status.update(label="產生會議摘要...")
        result = summarize(
            st.session_state.confirmed_transcript,
            participants=st.session_state.participants,
            progress_callback=lambda msg: status.write(f"⏳ {msg}")
        )
        if not result or not result.get("summary"):
            raise RuntimeError("AI 未回傳摘要內容，請稍後重試")

        summary = result["summary"]
        key_points = result.get("key_points", "")
        auto_tags = result.get("auto_tags", [])
        st.session_state.summary = summary
        st.session_state.summary_draft = summary
        st.session_state.key_points = key_points
        # 如果使用者沒有手動填標籤，就用 AI 自動產生的
        if not st.session_state.tags and auto_tags:
            st.session_state.tags = auto_tags

        # 清除 widget cache，讓編輯器顯示新的摘要內容
        for wkey in ['summary_editor', 'key_points_editor']:
            if wkey in st.session_state:
                del st.session_state[wkey]

        output_dir = Path(st.session_state.output_dir)
        (output_dir / "summary_draft.md").write_text(summary, encoding='utf-8')

        st.session_state.step = 2
        st.session_state.summarizing = False
        status.update(label="✅ 摘要已產生，請審閱", state="complete")

    except Exception as e:
        st.session_state.summarizing = False
        st.session_state.summarize_error = str(e)
        status.update(label="❌ 摘要產生失敗", state="error")
        status.write(f"❌ {str(e)}")


# ──────────────────────────────────────────────
# Step 2.5: 審閱摘要
# ──────────────────────────────────────────────

def _show_summary_review():
    if st.session_state.step != 2:
        return

    st.divider()
    st.header("📝 審閱摘要")

    # 顯示上一次摘要失敗的錯誤訊息
    if 'summarize_error' in st.session_state:
        st.error(f"❌ 摘要產生失敗：{st.session_state.summarize_error}")
        del st.session_state['summarize_error']

    st.info("👇 請檢查 AI 產生的摘要，可直接修改。確認無誤後按「上傳至 Notion」。")

    is_busy = st.session_state.summarizing

    edited_summary = st.text_area(
        "摘要內容（可編輯）",
        value=st.session_state.summary,
        height=500,
        key="summary_editor",
    )

    edited_key_points = st.text_input(
        "Highlights（可編輯）",
        value=st.session_state.key_points or "",
        key="key_points_editor",
    )

    with st.expander("📄 對照逐字稿", expanded=False):
        if st.session_state.confirmed_transcript:
            st.text_area(
                "逐字稿（唯讀）",
                st.session_state.confirmed_transcript,
                height=400,
                disabled=True,
                label_visibility="collapsed",
            )

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("✅ 確認上傳 Notion", type="primary", disabled=is_busy):
            st.session_state.summary = edited_summary
            st.session_state.key_points = edited_key_points
            _upload_to_notion(edited_summary, edited_key_points)
    with col2:
        btn_label = "⏳ 摘要產生中..." if is_busy else "🔄 重新產生摘要"
        if st.button(btn_label, disabled=is_busy):
            st.session_state.summarizing = True
            st.rerun()
    with col3:
        if st.button("⬅️ 回到逐字稿", disabled=is_busy):
            st.session_state.step = 1
            st.rerun()

    # 摘要產生中：按鈕已 disabled，在畫面底部才真正執行摘要
    if is_busy:
        _do_summarize()
        st.rerun()


# ──────────────────────────────────────────────
# Step 3: 上傳 Notion
# ──────────────────────────────────────────────

def _upload_to_notion(final_summary, final_key_points):
    from notion_uploader import ensure_database, upload_meeting

    output_dir = Path(st.session_state.output_dir)

    try:
        with st.spinner("上傳至 Notion 中..."):
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "summary.md").write_text(final_summary, encoding='utf-8')
            _save_feedback(output_dir, final_summary, final_key_points)

            db_id = ensure_database()
            transcript_to_upload = (
                st.session_state.confirmed_transcript
                or st.session_state.raw_transcript
            )
            page_url = upload_meeting(
                db_id,
                st.session_state.meeting_name,
                st.session_state.date_str,
                st.session_state.tags,
                final_summary,
                transcript_to_upload,
                key_points=final_key_points,
            )
            st.session_state.page_url = page_url
            st.session_state.step = 3
            st.rerun()
    except Exception as e:
        st.error(f"上傳失敗：{str(e)}")


# ──────────────────────────────────────────────
# Feedback
# ──────────────────────────────────────────────

def _save_feedback(output_dir, final_summary, final_key_points):
    draft = st.session_state.summary_draft or ""
    if draft == final_summary:
        return

    feedback = {
        "timestamp": datetime.now().isoformat(),
        "model": config.LLM_MODEL,
        "meeting_name": st.session_state.meeting_name,
        "transcript_length": len(st.session_state.confirmed_transcript or st.session_state.raw_transcript or ""),
        "draft_length": len(draft),
        "final_length": len(final_summary),
        "was_edited": True,
    }

    (output_dir / "feedback.json").write_text(
        json.dumps(feedback, ensure_ascii=False, indent=2), encoding='utf-8'
    )
    (output_dir / "summary_draft.md").write_text(draft, encoding='utf-8')
    (output_dir / "summary.md").write_text(final_summary, encoding='utf-8')

    feedback_log = config.BASE_DIR / "feedback_log.jsonl"
    with open(feedback_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(feedback, ensure_ascii=False) + "\n")


# ──────────────────────────────────────────────
# 結果顯示
# ──────────────────────────────────────────────

def _show_upload_result():
    if not st.session_state.page_url:
        return

    st.divider()
    st.header("📊 處理完成")

    tab_summary, tab_transcript = st.tabs(["📝 會議摘要", "📄 逐字稿"])

    with tab_summary:
        if st.session_state.summary:
            st.markdown(st.session_state.summary)

    with tab_transcript:
        transcript = st.session_state.confirmed_transcript or st.session_state.raw_transcript
        if transcript:
            st.text_area("逐字稿", transcript, height=400, disabled=True, label_visibility="collapsed")

    st.success("✅ 已上傳至 Notion")
    st.link_button("📝 開啟會議頁面", st.session_state.page_url)

    if st.session_state.output_dir:
        st.caption(f"📁 本地備份：{st.session_state.output_dir}")


if __name__ == "__main__":
    main()
