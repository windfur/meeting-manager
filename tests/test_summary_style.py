"""測試摘要規範系統的完整資料流。

驗證：
1. prompts/ 檔案都能正確讀取
2. _load_user_style() 的各種情境
3. _build_phase2_prompt() 的組合邏輯
4. 儲存/清除 cycle 後 prompt 正確切換
"""
import sys
from pathlib import Path

# 確保能 import 專案模組
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from summarizer import _read_prompt, _load_user_style, _build_phase2_prompt

PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name}" + (f" — {detail}" if detail else ""))


def test_prompt_files():
    print("\n🔍 測試 1：Prompt 檔案讀取")

    p1 = _read_prompt("phase1_analysis.md")
    check("phase1_analysis.md 可讀取", len(p1) > 100, f"只有 {len(p1)} 字")
    check("phase1_analysis.md 包含議題追蹤指令", "議題" in p1 or "分析" in p1 or "提案" in p1)

    p2_sys = _read_prompt("phase2_system.md")
    check("phase2_system.md 可讀取", len(p2_sys) > 50)
    check("phase2_system.md 包含 KEY_POINTS", "KEY_POINTS" in p2_sys)
    check("phase2_system.md 包含 TAGS", "TAGS" in p2_sys)

    p2_style = _read_prompt("phase2_default_style.md")
    check("phase2_default_style.md 可讀取", len(p2_style) > 200)
    check("phase2_default_style.md 包含輸出格式", "輸出格式" in p2_style)
    check("phase2_default_style.md 包含 ✅/❌/⏳", "✅" in p2_style and "❌" in p2_style and "⏳" in p2_style)


def test_no_user_style():
    print("\n🔍 測試 2：無使用者自訂 → 使用預設規範")

    # 確保 summary_style.md 不存在
    style_file = config.SUMMARY_STYLE_FILE
    backup = None
    if style_file.exists():
        backup = style_file.read_text(encoding='utf-8')
        style_file.unlink()

    try:
        user_style = _load_user_style()
        check("_load_user_style() 回傳空字串", user_style == "", f"回傳: '{user_style[:50]}'")

        prompt = _build_phase2_prompt(user_style)
        check("prompt 包含 phase2_system 內容", "KEY_POINTS" in prompt)
        check("prompt 包含預設 style", "輸出格式" in prompt)
        check("prompt 不包含「使用者自訂」標頭", "使用者自訂" not in prompt)
    finally:
        if backup is not None:
            style_file.write_text(backup, encoding='utf-8')


def test_with_user_style():
    print("\n🔍 測試 3：有使用者自訂 → 取代預設規範")

    style_file = config.SUMMARY_STYLE_FILE
    backup = None
    if style_file.exists():
        backup = style_file.read_text(encoding='utf-8')

    test_content = "## 語言規則\n- 全英文撰寫\n\n## 輸出格式\n- 用表格呈現"

    try:
        style_file.write_text(test_content, encoding='utf-8')

        user_style = _load_user_style()
        check("_load_user_style() 讀到自訂內容", user_style == test_content,
              f"回傳: '{user_style[:50]}'")

        prompt = _build_phase2_prompt(user_style)
        check("prompt 包含 phase2_system 內容", "KEY_POINTS" in prompt)
        check("prompt 包含使用者自訂內容", "全英文撰寫" in prompt)
        check("prompt 包含「使用者自訂」標頭", "使用者自訂" in prompt)
        check("prompt 不包含預設 style 的 Case 格式",
              "Case [編號]" not in prompt,
              "預設格式沒被取代！")
    finally:
        if backup is not None:
            style_file.write_text(backup, encoding='utf-8')
        elif style_file.exists():
            style_file.unlink()


def test_empty_file():
    print("\n🔍 測試 4：空白檔案 → 視為無自訂")

    style_file = config.SUMMARY_STYLE_FILE
    backup = None
    if style_file.exists():
        backup = style_file.read_text(encoding='utf-8')

    try:
        style_file.write_text("", encoding='utf-8')
        check("空白檔案 → _load_user_style() 回傳空字串", _load_user_style() == "")

        style_file.write_text("   \n\n  ", encoding='utf-8')
        check("只有空白的檔案 → _load_user_style() 回傳空字串", _load_user_style() == "")
    finally:
        if backup is not None:
            style_file.write_text(backup, encoding='utf-8')
        elif style_file.exists():
            style_file.unlink()


def test_save_clear_cycle():
    print("\n🔍 測試 5：儲存 → 清除 cycle")

    style_file = config.SUMMARY_STYLE_FILE
    backup = None
    if style_file.exists():
        backup = style_file.read_text(encoding='utf-8')

    try:
        # 模擬儲存
        test_content = "## 測試規範\n- 這是測試用的規範"
        style_file.write_text(test_content, encoding='utf-8')
        check("儲存後檔案存在", style_file.exists())
        check("儲存後內容正確", style_file.read_text(encoding='utf-8').strip() == test_content)

        # 模擬清除
        style_file.unlink()
        check("清除後檔案不存在", not style_file.exists())
        check("清除後 _load_user_style() 回傳空字串", _load_user_style() == "")

        # 清除後應該用預設 prompt
        prompt = _build_phase2_prompt(_load_user_style())
        check("清除後 prompt 回到預設（包含 Case 格式）", "Case" in prompt)
        check("清除後 prompt 不包含測試內容", "測試規範" not in prompt)
    finally:
        if backup is not None:
            style_file.write_text(backup, encoding='utf-8')
        elif style_file.exists():
            style_file.unlink()


def test_prompt_structure():
    print("\n🔍 測試 6：最終 prompt 結構完整性")

    # 無自訂
    prompt_default = _build_phase2_prompt("")
    check("預設 prompt 長度 > 500 字", len(prompt_default) > 500,
          f"只有 {len(prompt_default)} 字")

    # 有自訂
    prompt_custom = _build_phase2_prompt("## 我的規範\n- 精簡風格")
    check("自訂 prompt 包含 system intro", "KEY_POINTS" in prompt_custom)
    check("自訂 prompt 包含自訂內容", "精簡風格" in prompt_custom)
    check("自訂 prompt 比預設短（因為取代了預設 style）",
          len(prompt_custom) < len(prompt_default),
          f"自訂: {len(prompt_custom)}, 預設: {len(prompt_default)}")


if __name__ == "__main__":
    print("=" * 50)
    print("🧪 摘要規範系統 — 完整測試")
    print("=" * 50)

    test_prompt_files()
    test_no_user_style()
    test_with_user_style()
    test_empty_file()
    test_save_clear_cycle()
    test_prompt_structure()

    print("\n" + "=" * 50)
    total = PASS + FAIL
    if FAIL == 0:
        print(f"🎉 全部通過！{PASS}/{total}")
    else:
        print(f"⚠️ {FAIL} 個失敗，{PASS} 個通過（共 {total}）")
    print("=" * 50)
