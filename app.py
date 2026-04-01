import re
import json
import logging
import streamlit as st
from pathlib import Path
from datetime import date, datetime
import config

# ── Logging 設定：輸出到 console，過濾 API key ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


st.set_page_config(page_title="會議管理助手", page_icon="🎙️", layout="wide")


def main():
    st.title("🎙️ 會議管理助手")
    st.caption("上傳錄音 → 審閱逐字稿 → AI 摘要 → 審閱修改 → 存入 Notion")

    # --- 初始化 session state（sidebar 元件需要） ---
    for key in ['raw_transcript', 'confirmed_transcript', 'summary',
                'summary_draft', 'key_points', 'output_dir', 'page_url',
                'step', 'meeting_name', 'date_str', 'tags', 'participants',
                'replace_pairs_count', 'editor_version', 'summarizing', 'uploading',
                'summary_version_idx', 'draft_base_version', 'notion_target_page', 'notion_target_db']:
        if key not in st.session_state:
            st.session_state[key] = None
    if 'summary_versions' not in st.session_state:
        st.session_state.summary_versions = []
    for cache_key in ['notion_pages', 'notion_databases', 'notion_selected_page']:
        if cache_key not in st.session_state:
            st.session_state[cache_key] = None
    if st.session_state.step is None:
        st.session_state.step = 0
    if st.session_state.replace_pairs_count is None:
        st.session_state.replace_pairs_count = 1
    if st.session_state.editor_version is None:
        st.session_state.editor_version = 0
    if st.session_state.summarizing is None:
        st.session_state.summarizing = False
    if st.session_state.uploading is None:
        st.session_state.uploading = False
    if 'summary_editor_ver' not in st.session_state:
        st.session_state.summary_editor_ver = 0
    if 'meta_tags_input' not in st.session_state:
        st.session_state.meta_tags_input = ""
    if 'meta_participants_input' not in st.session_state:
        st.session_state.meta_participants_input = ""

    # 將 _do_summarize 產生的 pending 值套用到 widget key（在 widget 渲染前）
    if '_pending_meta_tags' in st.session_state:
        st.session_state.meta_tags_input = st.session_state._pending_meta_tags
        del st.session_state['_pending_meta_tags']

    # --- Sidebar（永遠顯示，不受 config check 阻塞） ---
    _show_notion_accounts()
    _show_meeting_browser()
    _show_style_settings()

    if not _check_config():
        return

    # 沒有 Notion 帳號時阻擋主流程
    if not config.load_notion_tokens():
        st.info("👈 請先在左側『🔑 Notion 帳號』新增至少一組 Token，才能開始使用。")
        return

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

    tags = _parse_comma_list(tags_input)
    participants = _parse_comma_list(participants_input)
    date_str = meeting_date.strftime('%Y-%m-%d')

    st.caption(f"🤖 摘要模型：`{config.LLM_MODEL}`（可在 .env 切換）")

    # --- Step 1: 轉錄按鈕 ---
    can_start = uploaded_file is not None and bool(meeting_name)
    if st.button("🚀 開始轉錄", type="primary", disabled=not can_start):
        st.session_state.meeting_name = meeting_name
        st.session_state.date_str = date_str
        st.session_state.tags = tags
        st.session_state.participants = participants
        st.session_state.meta_tags_input = ", ".join(tags)
        st.session_state.meta_participants_input = ", ".join(participants)
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
# Sidebar: 歷史會議瀏覽
# ──────────────────────────────────────────────

def _scan_meetings():
    """掃描 output/ 資料夾，回傳會議清單（按日期降序）。"""
    output_root = config.OUTPUT_DIR
    if not output_root.exists():
        return []

    meetings = []
    for d in output_root.iterdir():
        if not d.is_dir():
            continue
        # 資料夾格式：{YYYY-MM-DD}_{name}
        match = re.match(r'^(\d{4}-\d{2}-\d{2})_(.+)$', d.name)
        if not match:
            continue
        date_str = match.group(1)
        name = match.group(2)

        has_transcript = (d / "transcript_raw.txt").exists()
        has_draft = (d / "summary_draft.md").exists()
        has_uploaded = (d / "summary.md").exists()
        ver_count = len(list(d.glob("summary_v*.md")))

        # 讀取 uploaded_by（FR-004, FR-005 向下相容）
        uploaded_by = None
        meta_path = d / "meeting_meta.json"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding='utf-8'))
                uploaded_by = meta.get("uploaded_by")
            except (json.JSONDecodeError, KeyError):
                pass

        if has_uploaded:
            status = "🟢"
            status_text = f"已上傳（{uploaded_by}）" if uploaded_by else "已上傳"
        elif has_draft or ver_count > 0:
            status = "🟡"
            status_text = "草稿"
        elif has_transcript:
            status = "🔵"
            status_text = "僅逐字稿"
        else:
            continue  # 空資料夾跳過

        meetings.append({
            "path": d,
            "date": date_str,
            "name": name,
            "status": status,
            "status_text": status_text,
            "has_transcript": has_transcript,
            "has_draft": has_draft,
            "has_uploaded": has_uploaded,
            "ver_count": ver_count,
            "uploaded_by": uploaded_by,
        })

    meetings.sort(key=lambda m: m["date"], reverse=True)
    return meetings


def _show_meeting_browser():
    """側邊欄：歷史會議清單。"""
    with st.sidebar:
        with st.expander("📂 歷史會議", expanded=False):
            meetings = _scan_meetings()
            if not meetings:
                st.caption("尚無歷史會議")
                return

            # 日期篩選
            all_dates = sorted(set(m["date"] for m in meetings), reverse=True)
            date_options = ["全部"] + all_dates
            selected_date = st.selectbox(
                "依日期篩選",
                date_options,
                key="meeting_browser_date",
                label_visibility="collapsed",
            )
            if selected_date != "全部":
                meetings = [m for m in meetings if m["date"] == selected_date]

            # 帳號篩選（FR-006, FR-007 AND 日期篩選）
            account_labels = sorted(set(
                m["uploaded_by"] for m in meetings if m.get("uploaded_by")
            ))
            account_options = ["全部", "只看未上傳"] + account_labels
            # FR-010: 切換帳號時自動帶入篩選
            pending = st.session_state.pop("_pending_browser_account", None)
            if pending:
                if pending in account_options:
                    st.session_state.meeting_browser_account = pending
                else:
                    st.session_state.meeting_browser_account = "全部"
            selected_account = st.selectbox(
                "依帳號篩選",
                account_options,
                key="meeting_browser_account",
                label_visibility="collapsed",
            )
            if selected_account == "只看未上傳":
                meetings = [m for m in meetings if not m["has_uploaded"]]
            elif selected_account != "全部":
                meetings = [m for m in meetings if m.get("uploaded_by") == selected_account]

            st.caption(f"共 {len(meetings)} 場會議　🟢已上傳 🟡草稿 🔵僅逐字稿")

            for m in meetings:
                label = f"{m['status']}{m['status_text']} {m['date']}　{m['name']}"
                if m["ver_count"] > 0:
                    label += f"（{m['ver_count']}版）"
                if st.button(label, key=f"open_{m['path'].name}", use_container_width=True):
                    _resume_meeting(m)
                    st.rerun()


def _resume_meeting(meeting_info):
    """從磁碟載入一場既有會議，跳到對應步驟。"""
    output_dir = meeting_info["path"]

    # 重設所有 session state
    for key in ['raw_transcript', 'confirmed_transcript', 'summary',
                'summary_draft', 'key_points', 'page_url']:
        st.session_state[key] = None
    st.session_state.summary_versions = []
    st.session_state.summary_version_idx = None
    st.session_state.draft_base_version = None
    # 遞增版本號（而非重設為 0），確保 widget key 與上一場會議不同
    st.session_state.summary_editor_ver = st.session_state.get('summary_editor_ver', 0) + 1
    st.session_state.editor_version = st.session_state.get('editor_version', 0) + 1
    st.session_state.replace_pairs_count = 1
    st.session_state.summarizing = False
    st.session_state.uploading = False

    # 基本資訊
    st.session_state.output_dir = str(output_dir)
    st.session_state.meeting_name = meeting_info["name"]
    st.session_state.date_str = meeting_info["date"]

    # 載入逐字稿
    raw_path = output_dir / "transcript_raw.txt"
    if raw_path.exists():
        transcript = raw_path.read_text(encoding='utf-8')
        st.session_state.raw_transcript = transcript
        st.session_state.confirmed_transcript = transcript
        st.session_state.step = 1  # 預設到逐字稿審閱

    # 載入 metadata（tags, participants）
    meta_path = output_dir / "meeting_meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        st.session_state.tags = meta.get("tags", [])
        st.session_state.participants = meta.get("participants", [])
    # 預填 metadata 文字欄位（供 Step 1/2 的 text_input 綁定）
    st.session_state.meta_tags_input = ", ".join(st.session_state.tags or [])
    st.session_state.meta_participants_input = ", ".join(st.session_state.participants or [])

    # 載入摘要版本 + 草稿（會覆蓋 step 為 2）
    _load_versions_from_disk(output_dir)


# ──────────────────────────────────────────────
# Config check
# ──────────────────────────────────────────────

def _check_config():
    issues = []
    if not config.OPENAI_API_KEY:
        issues.append("缺少 OPENAI_API_KEY")
    if issues:
        st.error("⚠️ 設定不完整：\n" + "\n".join(f"- {i}" for i in issues))
        return False
    return True


# ──────────────────────────────────────────────
# Sidebar: Notion 帳號管理
# ──────────────────────────────────────────────

def _show_notion_accounts():
    """側邊欄：管理多個 Notion workspace tokens。"""
    import notion_uploader

    with st.sidebar:
        tokens = config.load_notion_tokens()
        with st.expander("🔑 Notion 帳號", expanded=not tokens):

            if tokens:
                # 選擇要用的帳號
                labels = [t["label"] for t in tokens]
                # 啟動時從磁碟還原上次選擇的帳號
                if "notion_token_idx" not in st.session_state:
                    saved_label = config.load_active_notion_account()
                    if saved_label and saved_label in labels:
                        st.session_state.notion_token_idx = labels.index(saved_label)
                    else:
                        st.session_state.notion_token_idx = 0
                current_idx = st.session_state.get("notion_token_idx", 0)
                if current_idx >= len(tokens):
                    current_idx = 0

                selected_idx = st.radio(
                    "使用帳號",
                    range(len(labels)),
                    format_func=lambda i: labels[i],
                    index=current_idx,
                    key="notion_account_radio",
                )

                # 切換帳號時重設頁面快取
                if selected_idx != st.session_state.get("notion_token_idx"):
                    st.session_state.notion_token_idx = selected_idx
                    st.session_state.notion_pages = None
                    st.session_state.notion_databases = None
                    # FR-010: 切換帳號時自動篩選歷史會議
                    st.session_state._pending_browser_account = labels[selected_idx]
                    # 持久化帳號選擇
                    config.save_active_notion_account(labels[selected_idx])

                # 設定 active token
                active_token = tokens[selected_idx]["token"]
                notion_uploader.set_token(active_token)
                st.session_state.active_notion_token = active_token

                st.caption(f"Token: ...{active_token[-6:]}")

                # 刪除按鈕（.env 的不能刪）
                if tokens[selected_idx]["label"] != "預設（.env）":
                    if st.button("🗑️ 移除此帳號", key="remove_notion_token"):
                        config.remove_notion_token(active_token)
                        st.session_state.notion_token_idx = 0
                        st.session_state.notion_pages = None
                        st.session_state.notion_databases = None
                        st.rerun()
            else:
                st.info("尚無 Notion 帳號，請在下方新增。")

            # 新增帳號
            st.divider()
            st.caption("新增 Notion 帳號")
            new_label = st.text_input("標籤", placeholder="例：公司、個人", key="new_notion_label")
            new_token = st.text_input("Token", placeholder="secret_...", type="password", key="new_notion_token")
            if st.button("➕ 新增", key="add_notion_token"):
                if new_label and new_token:
                    config.save_notion_token(new_label.strip(), new_token.strip())
                    st.session_state.notion_pages = None
                    st.session_state.notion_databases = None
                    st.rerun()
                else:
                    st.warning("請填入標籤和 Token")


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

        # 版本號：變更時 +1 強制 widget 重建
        if 'style_version' not in st.session_state:
            st.session_state.style_version = 0

        # 讀取現有內容
        current = ""
        if style_file.exists():
            current = style_file.read_text(encoding='utf-8').strip()

        # 產生範本按鈕（只在編輯器為空時顯示）
        if not current:
            if st.button("📋 產生規範範本", use_container_width=True,
                         help="一鍵填入結構化範本，你只需要修改內容"):
                style_file.write_text(STYLE_TEMPLATE, encoding='utf-8')
                st.session_state.style_version += 1
                st.rerun()

        style_key = f"style_editor_v{st.session_state.style_version}"
        edited = st.text_area(
            "摘要規範",
            value=current,
            height=350,
            placeholder="點擊上方「📋 產生規範範本」開始，\n或直接寫你的摘要規範。\n\n建議包含：語言規則、領域知識、寫作原則、\n結論標記準則、主題拆分、輸出格式。",
            key=style_key,
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 儲存", use_container_width=True):
                style_file.write_text(edited, encoding='utf-8')
                st.session_state.style_version += 1
                st.toast("✅ 摘要規範已儲存！")
                st.rerun()
        with col2:
            if st.button("🗑️ 清除", use_container_width=True):
                if style_file.exists():
                    style_file.unlink()
                st.session_state.style_version += 1
                st.toast("已清除！")
                st.rerun()

        if edited.strip():
            st.info("✅ 規範已啟用，下次產生摘要時會套用。")
        else:
            st.caption("目前使用預設摘要規範。")


# ──────────────────────────────────────────────
# Step 1: 轉錄（只做轉錄，不做摘要）
# ──────────────────────────────────────────────

def _load_versions_from_disk(output_dir: Path):
    """從磁碟載入歷史版本 (summary_v*.md) 和草稿 (summary_draft.md)。"""
    import re as _re

    # 載入 summary_v1.md, summary_v2.md, ...
    ver_files = sorted(output_dir.glob("summary_v*.md"),
                       key=lambda p: int(_re.search(r'summary_v(\d+)', p.stem).group(1)))
    versions = []
    for vf in ver_files:
        content = vf.read_text(encoding='utf-8')
        mtime = datetime.fromtimestamp(vf.stat().st_mtime).strftime("%H:%M:%S")
        versions.append({
            "summary": content,
            "key_points": "",
            "auto_tags": [],
            "timestamp": mtime,
        })

    if versions:
        st.session_state.summary_versions = versions
        st.session_state.summary_version_idx = len(versions) - 1

    # 載入草稿
    draft_path = output_dir / "summary_draft.md"
    if draft_path.exists():
        draft_raw = draft_path.read_text(encoding='utf-8')
        # 解析 base version 標記
        base_match = _re.match(r'<!-- draft_base_version: (\d+) -->\n', draft_raw)
        if base_match:
            st.session_state.draft_base_version = int(base_match.group(1))
            draft_text = draft_raw[base_match.end():]
        else:
            # 沒有標記時：如果有版本，預設為最後一版
            st.session_state.draft_base_version = len(versions) if versions else None
            draft_text = draft_raw

        st.session_state.summary = draft_text
        st.session_state.summary_draft = draft_text
        st.session_state.step = 2
    elif versions:
        # 沒有草稿但有版本 → 用最後一版
        last = versions[-1]
        st.session_state.summary = last["summary"]
        st.session_state.summary_draft = last["summary"]
        st.session_state.draft_base_version = len(versions)
        st.session_state.step = 2


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

            # 載入磁碟上的歷史版本 + 草稿
            _load_versions_from_disk(output_dir)
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
        _save_meeting_meta(output_dir)
        status.update(label="✅ 轉錄完成，請審閱逐字稿", state="complete")
        status.write(f"共 {len(raw_transcript):,} 字")

    except Exception as e:
        status.update(label="❌ 轉錄失敗", state="error")
        status.write(f"❌ {str(e)}")


# ──────────────────────────────────────────────
# Helper: 逗號分隔字串解析
# ──────────────────────────────────────────────

def _parse_comma_list(text: str) -> list[str]:
    """將逗號分隔字串解析為 list，自動 trim 並過濾空值。"""
    return [item.strip() for item in text.split(',') if item.strip()] if text else []


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

    # Metadata 欄位（標籤 + 參與者）
    is_busy_meta = st.session_state.summarizing or st.session_state.uploading
    meta_col1, meta_col2 = st.columns(2)
    with meta_col1:
        st.text_input("🏷️ 標籤（逗號分隔）", key="meta_tags_input", disabled=is_busy_meta)
    with meta_col2:
        st.text_input("👥 參與者（逗號分隔）", key="meta_participants_input", disabled=is_busy_meta)

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
                current = st.session_state.get(f"transcript_editor_v{st.session_state.editor_version}", st.session_state.raw_transcript)
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
    is_busy = st.session_state.summarizing or st.session_state.uploading
    cols = st.columns([1, 1, 2]) if has_summary else st.columns([1, 3])
    with cols[0]:
        btn_label = "⏳ 摘要產生中..." if is_busy else "✅ 確認逐字稿，產生摘要"
        if st.button(btn_label, type="primary", disabled=is_busy):
            # 同步 metadata
            st.session_state.tags = _parse_comma_list(st.session_state.meta_tags_input)
            st.session_state.participants = _parse_comma_list(st.session_state.meta_participants_input)
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
                # 同步 metadata
                st.session_state.tags = _parse_comma_list(st.session_state.meta_tags_input)
                st.session_state.participants = _parse_comma_list(st.session_state.meta_participants_input)
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

    transcript_len = len(st.session_state.confirmed_transcript or "")
    participants = st.session_state.participants
    logger.info("使用者觸發摘要 | 逐字稿長度=%d | 參與者=%s", transcript_len, participants)

    status = st.status("產生摘要中...", expanded=True)

    try:
        status.update(label="產生會議摘要...")
        result = summarize(
            st.session_state.confirmed_transcript,
            participants=participants,
            progress_callback=lambda msg: status.write(f"⏳ {msg}")
        )
        if not result or not result.get("summary"):
            logger.error("摘要結果為空 | result=%s", result)
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
            # 透過 _pending 避免 widget 已渲染後直接賦值報錯
            st.session_state._pending_meta_tags = ", ".join(auto_tags)

        # 儲存此版本到歷史紀錄（記憶體 + 磁碟）
        ver = {
            "summary": summary,
            "key_points": key_points,
            "auto_tags": auto_tags,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }
        st.session_state.summary_versions.append(ver)
        ver_num = len(st.session_state.summary_versions)
        st.session_state.summary_version_idx = ver_num - 1
        st.session_state.draft_base_version = ver_num

        # 寫入磁碟：summary_v{N}.md + summary_draft.md
        output_dir = Path(st.session_state.output_dir)
        (output_dir / f"summary_v{ver_num}.md").write_text(summary, encoding='utf-8')
        draft_content = f"<!-- draft_base_version: {ver_num} -->\n" + summary
        (output_dir / "summary_draft.md").write_text(draft_content, encoding='utf-8')

        # 遞增 widget 版本號，強制 Streamlit 重建編輯器
        st.session_state.summary_editor_ver += 1

        st.session_state.step = 2
        st.session_state.summarizing = False
        status.update(label="✅ 摘要已產生，請審閱", state="complete")
        logger.info("摘要產生成功 | 摘要長度=%d | 版本=%d", len(summary), ver_num)

    except Exception as e:
        st.session_state.summarizing = False
        st.session_state.summarize_error = str(e)
        logger.error("摘要產生失敗 | %s: %s", type(e).__name__, str(e), exc_info=True)
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

    # 顯示上一次上傳失敗的錯誤訊息
    if 'upload_error' in st.session_state:
        st.error(f"❌ 上傳失敗：{st.session_state.upload_error}")
        del st.session_state['upload_error']

    is_busy = st.session_state.summarizing or st.session_state.uploading

    # Metadata 欄位（標籤 + 參與者）
    meta_col1, meta_col2 = st.columns(2)
    with meta_col1:
        st.text_input("🏷️ 標籤（逗號分隔）", key="meta_tags_input", disabled=is_busy)
    with meta_col2:
        st.text_input("👥 參與者（逗號分隔）", key="meta_participants_input", disabled=is_busy)
    versions = st.session_state.summary_versions

    # 版本選擇器（2 個以上版本時顯示）
    if len(versions) > 1:
        labels = [f"第 {i+1} 版（{v['timestamp']}）" for i, v in enumerate(versions)]
        current_idx = st.session_state.summary_version_idx or 0
        selected = st.radio(
            "📋 摘要版本",
            range(len(labels)),
            format_func=lambda i: labels[i],
            index=current_idx,
            horizontal=True,
            key="version_selector",
            disabled=is_busy,
        )
        if selected != st.session_state.summary_version_idx:
            ver = versions[selected]
            st.session_state.summary = ver["summary"]
            st.session_state.key_points = ver["key_points"]
            st.session_state.summary_version_idx = selected
            st.session_state.draft_base_version = selected + 1
            st.session_state.summary_editor_ver += 1
            st.rerun()
        st.caption(f"共 {len(versions)} 個版本，選擇後可再編輯，最後按「上傳」即為最終版")
    else:
        st.info("👇 請檢查 AI 產生的摘要，可直接修改。確認無誤後按「上傳至 Notion」。")

    base_ver = st.session_state.draft_base_version
    if base_ver:
        st.caption(f"📌 目前草稿基於第 {base_ver} 版 AI 摘要")

    sev = st.session_state.summary_editor_ver
    edited_summary = st.text_area(
        "摘要內容（可編輯）",
        value=st.session_state.summary,
        height=500,
        key=f"summary_editor_v{sev}",
        disabled=is_busy,
    )

    edited_key_points = st.text_input(
        "Highlights（可編輯）",
        value=st.session_state.key_points or "",
        key=f"key_points_editor_v{sev}",
        disabled=is_busy,
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

    # Notion 目標頁面選擇
    _show_notion_page_selector(disabled=is_busy)

    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        target = st.session_state.notion_target_page
        upload_disabled = is_busy or not target
        if st.button("✅ 確認上傳 Notion", type="primary", disabled=upload_disabled):
            # 同步 metadata
            st.session_state.tags = _parse_comma_list(st.session_state.meta_tags_input)
            st.session_state.participants = _parse_comma_list(st.session_state.meta_participants_input)
            st.session_state.summary = edited_summary
            st.session_state.key_points = edited_key_points
            st.session_state.uploading = True
            st.rerun()
    with col2:
        if st.button("💾 儲存草稿", disabled=is_busy):
            # 同步 metadata
            st.session_state.tags = _parse_comma_list(st.session_state.meta_tags_input)
            st.session_state.participants = _parse_comma_list(st.session_state.meta_participants_input)
            output_dir = Path(st.session_state.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            draft_content = edited_summary
            base_ver = st.session_state.draft_base_version
            if base_ver:
                header = f"<!-- draft_base_version: {base_ver} -->\n"
                draft_content = header + edited_summary
            (output_dir / "summary_draft.md").write_text(draft_content, encoding='utf-8')
            st.session_state.summary = edited_summary
            st.session_state.key_points = edited_key_points
            _save_meeting_meta(output_dir)
            st.toast("✅ 草稿已儲存！下次開啟同一場會議時會自動載入。")
    with col3:
        btn_label = "⏳ 摘要產生中..." if is_busy else "🔄 重新產生摘要"
        if st.button(btn_label, disabled=is_busy):
            st.session_state.summarizing = True
            st.rerun()
    with col4:
        if st.button("⬅️ 回到逐字稿", disabled=is_busy):
            st.session_state.step = 1
            st.rerun()

    # 上傳中：在畫面底部才真正執行上傳
    if st.session_state.uploading:
        _upload_to_notion(st.session_state.summary, st.session_state.key_points)

    # 摘要產生中：按鈕已 disabled，在畫面底部才真正執行摘要
    if st.session_state.summarizing:
        _do_summarize()
        st.rerun()


# ──────────────────────────────────────────────
# Notion 頁面選擇
# ──────────────────────────────────────────────

def _show_notion_page_selector(disabled=False):
    """讓使用者選擇要上傳到 Notion 的哪個頁面和資料庫。"""
    if not st.session_state.get("active_notion_token"):
        st.info("請先在左側「🔑 Notion 帳號」新增 Token，才能選擇上傳頁面。")
        return

    from notion_uploader import search_pages, list_databases

    # 快取頁面清單
    if st.session_state.notion_pages is None:
        with st.spinner("讀取 Notion 頁面..."):
            st.session_state.notion_pages = search_pages()

    pages = st.session_state.notion_pages

    if not pages:
        st.warning("⚠️ 找不到可用的 Notion 頁面。請確認 Integration 已加入至少一個頁面。")
        return

    # ── 第一層：選頁面 ──
    page_options = {p["id"]: p["title"] for p in pages}
    page_ids = list(page_options.keys())

    default_idx = 0
    default_page = config.NOTION_PARENT_PAGE_ID
    if default_page and default_page in page_ids:
        default_idx = page_ids.index(default_page)

    col_page, col_refresh = st.columns([4, 1])
    with col_page:
        selected_page = st.selectbox(
            "📄 Notion 頁面",
            options=page_ids,
            format_func=lambda pid: page_options[pid],
            index=default_idx,
            key="notion_page_selector",
            disabled=disabled,
        )
    with col_refresh:
        st.write("")
        st.write("")
        if st.button("🔄", help="重新載入頁面清單", disabled=disabled):
            st.session_state.notion_pages = None
            st.session_state.notion_databases = None
            st.session_state.notion_selected_page = None
            st.rerun()

    # 頁面切換時重新載入 databases
    if st.session_state.get("notion_selected_page") != selected_page:
        st.session_state.notion_selected_page = selected_page
        st.session_state.notion_databases = None

    # ── 第二層：選資料庫 ──
    if st.session_state.get("notion_databases") is None:
        with st.spinner("讀取資料庫..."):
            st.session_state.notion_databases = list_databases(selected_page)

    databases = st.session_state.notion_databases
    NEW_DB_SENTINEL = "__create_new__"

    if databases:
        db_options = {d["id"]: d["title"] for d in databases}
        db_options[NEW_DB_SENTINEL] = "➕ 建立新的會議知識庫"
        db_ids = list(db_options.keys())

        selected_db = st.selectbox(
            "🗄️ 資料庫",
            options=db_ids,
            format_func=lambda did: db_options[did],
            key="notion_db_selector",
            disabled=disabled,
        )
    else:
        st.caption("📂 此頁面尚無資料庫，上傳時將自動建立「會議知識庫」")
        selected_db = NEW_DB_SENTINEL

    st.session_state.notion_target_page = selected_page
    st.session_state.notion_target_db = selected_db


# ──────────────────────────────────────────────
# Step 3: 上傳 Notion
# ──────────────────────────────────────────────

def _upload_to_notion(final_summary, final_key_points):
    from notion_uploader import create_database, upload_meeting, set_token

    # 確保使用正確的 token
    active_token = st.session_state.get("active_notion_token")
    if active_token:
        set_token(active_token)

    output_dir = Path(st.session_state.output_dir)

    try:
        with st.status("上傳至 Notion 中...", expanded=True) as status:
            status.update(label="儲存本地備份...", state="running")
            output_dir.mkdir(parents=True, exist_ok=True)
            (output_dir / "summary.md").write_text(final_summary, encoding='utf-8')
            # 同時更新草稿檔為最終上傳版
            draft_content = final_summary
            base_ver = st.session_state.draft_base_version
            if base_ver:
                draft_content = f"<!-- draft_base_version: {base_ver} -->\n" + final_summary
            (output_dir / "summary_draft.md").write_text(draft_content, encoding='utf-8')
            _save_meeting_meta(output_dir)
            _save_feedback(output_dir, final_summary, final_key_points)

            status.update(label="連線 Notion 資料庫...", state="running")
            target_page = st.session_state.notion_target_page
            db_id = st.session_state.get("notion_target_db")

            if not db_id or db_id == "__create_new__":
                status.update(label="建立新資料庫...", state="running")
                db_id = create_database(target_page)
                st.session_state.notion_databases = None  # 下次重新載入
            transcript_to_upload = (
                st.session_state.confirmed_transcript
                or st.session_state.raw_transcript
            )

            def _progress(msg):
                status.update(label=msg, state="running")

            page_url = upload_meeting(
                db_id,
                st.session_state.meeting_name,
                st.session_state.date_str,
                st.session_state.tags,
                final_summary,
                transcript_to_upload,
                key_points=final_key_points,
                progress_callback=_progress,
            )
            st.session_state.page_url = page_url
            # 記錄上傳帳號 label（FR-001, FR-003）
            tokens = config.load_notion_tokens()
            token_idx = st.session_state.get("notion_token_idx", 0)
            account_label = tokens[token_idx]["label"] if token_idx < len(tokens) else None
            _save_meeting_meta(output_dir, uploaded_by=account_label)
            st.session_state.uploading = False
            st.session_state.step = 3
            status.update(label="上傳完成！", state="complete")
            st.rerun()
    except Exception as e:
        st.session_state.upload_error = str(e)
        st.session_state.uploading = False
        st.rerun()


# ──────────────────────────────────────────────
# Feedback
# ──────────────────────────────────────────────

def _save_meeting_meta(output_dir, uploaded_by=None):
    """儲存會議 metadata（tags, participants）到磁碟。"""
    output_dir = Path(output_dir)
    meta = {
        "meeting_name": st.session_state.meeting_name,
        "date": st.session_state.date_str,
        "tags": st.session_state.tags or [],
        "participants": st.session_state.participants or [],
    }
    if uploaded_by is not None:
        meta["uploaded_by"] = uploaded_by
    # 保留既有的 uploaded_by（重新儲存草稿時不覆蓋）
    meta_path = output_dir / "meeting_meta.json"
    if uploaded_by is None and meta_path.exists():
        try:
            existing = json.loads(meta_path.read_text(encoding='utf-8'))
            if "uploaded_by" in existing:
                meta["uploaded_by"] = existing["uploaded_by"]
        except (json.JSONDecodeError, KeyError):
            pass
    meta_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8'
    )


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
