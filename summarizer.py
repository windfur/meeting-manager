import time
from pathlib import Path
from openai import OpenAI
import config


# ── Prompt 檔案路徑 ──
PROMPTS_DIR = Path(__file__).parent / "prompts"


def _read_prompt(filename: str) -> str:
    """從 prompts/ 讀取 prompt 檔案。"""
    return (PROMPTS_DIR / filename).read_text(encoding='utf-8').strip()


def _load_user_style():
    """讀取使用者自訂的摘要規範。"""
    style_file = config.SUMMARY_STYLE_FILE
    if style_file.exists():
        text = style_file.read_text(encoding='utf-8').strip()
        if text:
            return text
    return ""


def _build_phase2_prompt(user_style: str) -> str:
    """組合 Phase 2 system prompt。

    系統指令（角色 + KEY_POINTS/TAGS 格式）永遠存在；
    規則與格式部分：有使用者自訂就用自訂，沒有就用預設。
    """
    system_intro = _read_prompt("phase2_system.md")
    if user_style:
        return (
            system_intro
            + "\n\n## 使用者自訂的規則與偏好（請優先遵守，取代預設規則與格式）\n\n"
            + user_style
        )
    else:
        default_style = _read_prompt("phase2_default_style.md")
        return system_intro + "\n\n" + default_style


def _call_api(client, model, messages, progress_callback=None, phase_label=""):
    """呼叫 OpenAI API，含重試邏輯。"""
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=32768,
            )
            content = response.choices[0].message.content
            if content is None:
                finish = getattr(response.choices[0], 'finish_reason', 'unknown')
                raise RuntimeError(
                    f"{phase_label} API 回傳空白內容（finish_reason: {finish}）"
                )
            return content
        except Exception as e:
            error_str = str(e).lower()
            if "rate_limit" in error_str or "429" in error_str:
                wait = 10
                if progress_callback:
                    progress_callback(f"{phase_label} API 速率限制，等待 {wait} 秒後重試...")
                time.sleep(wait)
            elif attempt < 2:
                time.sleep((attempt + 1) * 3)
            else:
                raise RuntimeError(f"{phase_label} 失敗（重試 3 次）：{str(e)}")

    raise RuntimeError(f"{phase_label} 失敗：API 速率限制，請稍後再試")


def summarize(transcript: str, participants=None, progress_callback=None) -> dict:
    """兩階段摘要：先追蹤議題結論，再撰寫正式會議紀錄。"""
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    model = config.LLM_MODEL

    # 組合參與者資訊
    participant_note = ""
    if participants:
        names = "、".join(participants)
        participant_note = f"\n\n【參考資訊】本次會議參與者：{names}\n（請在摘要中盡可能辨識發言者，如果逐字稿中能對應到的話）"

    # ── 第一階段：議題結論追蹤 ──
    if progress_callback:
        progress_callback("【階段 1/2】正在追蹤每個議題的結論...")

    analysis = _call_api(
        client, model,
        messages=[
            {"role": "system", "content": _read_prompt("phase1_analysis.md")},
            {"role": "user", "content": f"以下是會議逐字稿，請按時間軸追蹤每個議題的結論：{participant_note}\n\n{transcript}"},
        ],
        progress_callback=progress_callback,
        phase_label="【階段 1】",
    )

    # ── 第二階段：根據分析撰寫正式摘要 ──
    if progress_callback:
        progress_callback("【階段 2/2】正在根據分析撰寫正式摘要...")

    # 讀取使用者自訂偏好，組合 Phase 2 prompt
    user_style = _load_user_style()
    phase2_prompt = _build_phase2_prompt(user_style)
    if user_style and progress_callback:
        progress_callback("已載入使用者自訂摘要規範。")

    content = _call_api(
        client, model,
        messages=[
            {"role": "system", "content": phase2_prompt},
            {"role": "user", "content": (
                f"以下是第一階段的「議題結論追蹤」：\n\n{analysis}\n\n"
                f"---\n\n以下是原始逐字稿（供你核對細節用）：{participant_note}\n\n{transcript}"
            )},
        ],
        progress_callback=progress_callback,
        phase_label="【階段 2】",
    )

    # 分離 KEY_POINTS 和 TAGS
    summary = content
    key_points = ""
    auto_tags = []
    lines_to_remove = []
    for line in content.split('\n'):
        stripped = line.strip()
        if stripped.startswith("KEY_POINTS:"):
            key_points = stripped.replace("KEY_POINTS:", "").strip()
            lines_to_remove.append(line)
        elif stripped.startswith("TAGS:"):
            raw_tags = stripped.replace("TAGS:", "").strip()
            auto_tags = [t.strip() for t in raw_tags.split(',') if t.strip()]
            lines_to_remove.append(line)
    for line in lines_to_remove:
        summary = summary.replace(line, "")
    summary = summary.rstrip()

    return {"summary": summary, "key_points": key_points, "auto_tags": auto_tags}
