import time
import httpx
import config

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# 當前使用的 token（可由 app.py 動態切換）
_active_token = None


def set_token(token):
    """設定當前要使用的 Notion token。"""
    global _active_token
    _active_token = token


def _get_token():
    return _active_token or config.NOTION_TOKEN


def _headers():
    return {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


def _api_post(path, payload, max_retries=3):
    """POST 到 Notion API，自動重試。"""
    for attempt in range(max_retries):
        resp = httpx.post(f"{NOTION_API}{path}", headers=_headers(), json=payload, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", (attempt + 1) * 5))
            time.sleep(wait)
            continue
        if attempt < max_retries - 1 and resp.status_code >= 500:
            time.sleep((attempt + 1) * 3)
            continue
        # 最終失敗
        raise RuntimeError(f"Notion API 錯誤 ({resp.status_code}): {resp.text[:500]}")
    raise RuntimeError("Notion API 重試次數已達上限")


def _api_patch(path, payload, max_retries=3):
    """PATCH 到 Notion API，自動重試。"""
    for attempt in range(max_retries):
        resp = httpx.patch(f"{NOTION_API}{path}", headers=_headers(), json=payload, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", (attempt + 1) * 5))
            time.sleep(wait)
            continue
        if attempt < max_retries - 1 and resp.status_code >= 500:
            time.sleep((attempt + 1) * 3)
            continue
        raise RuntimeError(f"Notion API 錯誤 ({resp.status_code}): {resp.text[:500]}")


def _api_get(path):
    """GET Notion API。"""
    resp = httpx.get(f"{NOTION_API}{path}", headers=_headers(), timeout=30)
    if resp.status_code == 200:
        return resp.json()
    return None


def create_database(parent_page_id):
    """在指定頁面下建立新的會議知識庫 Database，回傳 database_id。"""
    result = _api_post("/databases", {
        "parent": {"type": "page_id", "page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": "會議知識庫"}}],
        "properties": {
            "Name": {"title": {}},
            "Highlights": {"rich_text": {}},
            "Tags": {"multi_select": {"options": []}},
            "Date": {"date": {}},
        },
    })
    return result["id"]


def list_databases(parent_page_id):
    """列出指定頁面底下的所有 Database，回傳 [{id, title}]。"""
    results = []
    resp = _api_get(f"/blocks/{parent_page_id}/children?page_size=100")
    if not resp:
        return results
    for block in resp.get("results", []):
        if block.get("type") == "child_database":
            db_id = block["id"]
            title = block.get("child_database", {}).get("title", "未命名資料庫")
            results.append({"id": db_id, "title": title})
    return results


def search_pages():
    """搜尋 Integration 有權限存取的頁面，回傳 [{id, title}]。"""
    results = []
    payload = {"filter": {"value": "page", "property": "object"}, "page_size": 50}
    data = _api_post("/search", payload)
    if not data:
        return results
    for page in data.get("results", []):
        if page.get("in_trash"):
            continue
        title_parts = page.get("properties", {}).get("title", {}).get("title", [])
        if not title_parts:
            # 嘗試從 page 的 title 欄位取得名稱
            for prop in page.get("properties", {}).values():
                if prop.get("type") == "title" and prop.get("title"):
                    title_parts = prop["title"]
                    break
        title = "".join(t.get("plain_text", "") for t in title_parts) if title_parts else "未命名頁面"
        results.append({"id": page["id"], "title": title})
    return results


def upload_meeting(db_id, meeting_name, date_str, tags, summary_md, transcript_text,
                   key_points="", progress_callback=None):
    """上傳一場會議為單一頁面：摘要 + 收合的逐字稿。回傳 page_url。"""
    tag_list = [{"name": t.strip()} for t in tags if t.strip()]

    if progress_callback:
        progress_callback("組裝 Notion 頁面...")

    # 組裝 page 內容：摘要 blocks + 分隔線 + 逐字稿 toggle
    summary_blocks = _markdown_to_blocks(summary_md)
    transcript_blocks = _text_to_blocks(transcript_text)

    # toggle block 裡最多放 100 個 children，剩下的之後 append
    toggle_children = transcript_blocks[:100]
    toggle_block = {
        "object": "block",
        "type": "toggle",
        "toggle": {
            "rich_text": [{"type": "text", "text": {"content": "📄 完整逐字稿（點擊展開）"}}],
            "children": toggle_children,
        },
    }

    # page children = 摘要 + 分隔線 + toggle（Notion 限制最多 100 個 children）
    divider = {"object": "block", "type": "divider", "divider": {}}
    page_blocks = summary_blocks[:98] + [divider, toggle_block]

    if progress_callback:
        progress_callback("上傳至 Notion...")

    page = _api_post("/pages", {
        "parent": {"database_id": db_id},
        "properties": {
            "Name": {"title": [{"text": {"content": meeting_name}}]},
            "Highlights": {"rich_text": [{"text": {"content": key_points[:2000]}}]},
            "Tags": {"multi_select": tag_list},
            "Date": {"date": {"start": date_str}},
        },
        "children": page_blocks,
    })
    page_url = page["url"]
    page_id = page["id"]

    # 補上傳超過 98 個的摘要 blocks（極長摘要才會觸發）
    if len(summary_blocks) > 98:
        _append_blocks_batched(page_id, summary_blocks[98:], progress_callback=progress_callback)

    # 補上傳超過 100 個的逐字稿 blocks 到 toggle 裡
    if len(transcript_blocks) > 100:
        if progress_callback:
            progress_callback("逐字稿較長，分批上傳中...")
        # 找到 toggle block 的 id
        children_resp = _api_get(f"/blocks/{page_id}/children?page_size=100")
        toggle_id = None
        if children_resp:
            for block in children_resp.get("results", []):
                if block.get("type") == "toggle":
                    toggle_id = block["id"]
                    break
        if toggle_id:
            _append_blocks_batched(toggle_id, transcript_blocks[100:], progress_callback=progress_callback)

    return page_url


# --- 內部函式 ---

def _append_blocks_batched(page_id, blocks, batch_size=100, progress_callback=None):
    """分批附加 blocks（Notion 每次最多 100 個）。"""
    total = (len(blocks) + batch_size - 1) // batch_size
    for idx, i in enumerate(range(0, len(blocks), batch_size), 1):
        if progress_callback:
            progress_callback(f"分批上傳中... ({idx}/{total})")
        batch = blocks[i:i + batch_size]
        _api_patch(f"/blocks/{page_id}/children", {"children": batch})


def _markdown_to_blocks(md_text):
    """將 markdown 轉為 Notion block 列表。"""
    import re as _re
    blocks = []
    for line in md_text.split('\n'):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('#### '):
            blocks.append(_heading3_block(stripped[5:]))
        elif stripped.startswith('### '):
            blocks.append(_heading3_block(stripped[4:]))
        elif stripped.startswith('## '):
            blocks.append(_heading2_block(stripped[3:]))
        elif stripped.startswith('- ') or stripped.startswith('* '):
            blocks.append(_rich_bullet_block(stripped[2:]))
        elif _re.match(r'^\d+\.\s', stripped):
            text = _re.sub(r'^\d+\.\s', '', stripped)
            blocks.append(_numbered_block(text))
        else:
            for chunk in _split_text(stripped):
                blocks.append(_rich_paragraph_block(chunk))
    return blocks


def _text_to_blocks(text):
    """將逐字稿文字轉為 Notion paragraph blocks。"""
    blocks = []
    for line in text.split('\n'):
        stripped = line.strip()
        if not stripped:
            continue
        for chunk in _split_text(stripped):
            blocks.append(_paragraph_block(chunk))
    return blocks


def _split_text(text, max_len=2000):
    """依 Notion 2000 字元限制切割文字。"""
    if len(text) <= max_len:
        return [text]
    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        split_at = text.rfind(' ', 0, max_len)
        if split_at == -1:
            split_at = text.rfind('，', 0, max_len)
        if split_at == -1:
            split_at = text.rfind('。', 0, max_len)
        if split_at == -1:
            split_at = max_len
        chunks.append(text[:split_at + 1])
        text = text[split_at + 1:].lstrip()
    return chunks


def _heading2_block(text):
    return {
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}]
        },
    }


def _heading3_block(text):
    return {
        "object": "block",
        "type": "heading_3",
        "heading_3": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}]
        },
    }


def _paragraph_block(text):
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": text[:2000]}}]
        },
    }


def _parse_rich_text(text):
    """解析 markdown 粗體（**text**）為 Notion rich_text 陣列。"""
    import re
    parts = re.split(r'(\*\*[^*]+\*\*)', text)
    rich_text = []
    for part in parts:
        if not part:
            continue
        if part.startswith('**') and part.endswith('**'):
            content = part[2:-2]
            rich_text.append({
                "type": "text",
                "text": {"content": content[:2000]},
                "annotations": {"bold": True},
            })
        else:
            rich_text.append({
                "type": "text",
                "text": {"content": part[:2000]},
            })
    return rich_text or [{"type": "text", "text": {"content": ""}}]


def _rich_bullet_block(text):
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": _parse_rich_text(text)},
    }


def _rich_paragraph_block(text):
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {"rich_text": _parse_rich_text(text)},
    }


def _numbered_block(text):
    return {
        "object": "block",
        "type": "numbered_list_item",
        "numbered_list_item": {"rich_text": _parse_rich_text(text)},
    }
