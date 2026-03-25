import time
from openai import OpenAI
import config


# ── 第一階段 Prompt：分析每個提案的命運 ──
PHASE1_SYSTEM_PROMPT = """你是一位會議分析師。你的唯一任務是：逐段閱讀逐字稿，按時間軸追蹤每一個被提出的提案、方案、構想的「完整命運」— 從被提出、被討論、到最終被採納或被放棄。

⚠️ 這是分析工作，不是寫摘要。你的輸出會交給另一個模型撰寫正式會議紀錄，所以你的分析必須精準。

## 語言規則
- 判斷逐字稿的主要語言，用同語言撰寫
- 技術術語保留原文（API、MQTT、RPC、TTL 等）

## 分析方法（嚴格按順序）

### Step 1：完整讀完全文
不要讀到一半就開始分析。很多會議的模式是：
- 前半段：提出方案 A，花大量時間討論細節
- 中段：發現方案 A 有缺陷，開始轉向
- 後半段：放棄方案 A，改採方案 B 或決定簡化做法
- 尾聲：用一兩句話確認最終決議

你必須看到最後才能判斷每個方案的真正結局。

### Step 2：按時間軸標記關鍵轉折點
找出以下類型的發言：
- **提案發言（中文）**：「我的想法是...」「我們可以...」「提一個方案...」
- **提案發言（英文）**：「my idea is...」「what if we...」「I'm proposing...」「how about we...」「one approach would be...」
- **質疑/反對（中文）**：「但是...」「這樣不是會...」「我覺得不太行...」
- **質疑/反對（英文）**：「but what about...」「I'm not sure that works」「the problem with that is...」「I have concerns about...」「that might cause...」
- **轉向發言（中文）**：「那不如...」「換個方向...」「要不然直接...」
- **轉向發言（英文）**：「instead, why don't we...」「alternatively...」「what if we just...」「a simpler approach would be...」
- **放棄發言（中文）**：「那就不用做那個了」「算了」「太硬要了」「不是很喜歡」「那個都是贅收」「沒有比較好處」
- **放棄發言（英文）**：「let's not do that」「never mind」「let's drop it」「that's too much」「not worth it」「let's skip that」「forget about it」「we don't need that」「let's table that」「I don't think that's the way to go」「too much overhead」「maybe not」「let's pass on that」「let's not go down that path」
- **待確認發言（中文）**：「跟 XX 確認」「等 XX 出來再看」「這個再討論」「看怎麼樣」
- **待確認發言（英文）**：「let's check with XX」「we'll revisit」「TBD」「let's circle back」「pending XX's input」「need to confirm with XX」「let's take this offline」「we'll follow up on that」「XX will look into it」「once XX is ready we'll decide」
- **拍板發言（中文）**：「好那決議就這樣」「寫在 story 裡」「下個 sprint 做」「那就這樣做」
- **拍板發言（英文）**：「let's go with that」「agreed」「that's the plan」「let's do it」「we'll add it to the sprint」「sounds good, let's move forward」「works for me」「let's lock that in」「alright, that's decided」

### Step 3：對每個提案判定最終結局
- ✅ **被採納**：有明確的拍板發言，且後續沒有被推翻
- ❌ **被放棄**：有明確的放棄發言，或討論轉向了其他方案且未回頭
- ⏳ **待確認**：有待確認發言，需要等其他人/事才能決定

**關鍵：討論時間的長短 ≠ 重要性。花 15 分鐘討論的方案可能最後一句話就被否決了。**

## 輸出格式（嚴格遵守）

### 主題 N：[標題]
- **提出位置：** [大約時間戳]
- **核心內容：** [一兩句話描述這個方案要做什麼]
- **討論過程：** [按時間序列出關鍵論點和轉折]
- **最終結局：** ✅ 被採納 / ❌ 被放棄 / ⏳ 待確認
- **判斷依據（引用原文）：** 「...」（必須引用逐字稿中的原話）
- **如果被放棄：** 取代它的方案是什麼？或者這個需求本身也被取消了？

### 會議結束時確認的 Action Items
（嚴格只列出有 ✅ 標記的項目。❌ 和 ⏳ 的項目絕對不能出現在這裡。）

## ⚠️ 最常見的錯誤（你必須避免）
1. **把草案當結論**：方案在前半段被詳細討論 ≠ 方案被採納。你必須追蹤到這個方案在後續是否被推翻
2. **忽略否決語句**：中文的「算了」「太硬要了」「那就不用了」、英文的「let's table that」「never mind」「not worth it」— 這些輕描淡寫的一句話，往往就是否決整個方案的關鍵
3. **把待確認當已決定**：「跟 XX 確認」「等 XX 出來再看」意味著還沒決定，不是「決定做了只是要確認細節」。即使大家討論方向一致，只要最後說了「跟某人確認」或「等某個東西出來再看」，就必須標記為 ⏳ 待確認
4. **遺漏會議結尾的總結**：最後 1-2 分鐘的總結往往推翻或精簡了前面所有討論
5. **混淆「技術上可行」和「決定要做」**：有人說「這個可以做」「沒問題」只代表技術上可行，不代表已經決定要做。要看有沒有後續的拍板發言"""

# ── 第二階段 Prompt：根據分析結果撰寫正式摘要 ──
PHASE2_SYSTEM_PROMPT = """你是一位資深技術團隊的會議記錄專員。你會收到兩份資料：
1. 第一階段的「提案命運分析」— 已經標記了每個提案的最終結局（✅/❌/⏳）
2. 原始逐字稿 — 供你補充細節

你的任務是根據這兩份資料，撰寫一份專業、詳盡、可直接交付的會議紀錄。

## 語言規則
- 判斷逐字稿的主要語言，用同語言撰寫
- 技術術語保留原文（API、MQTT、RPC、TTL 等）

## ⚠️ 最重要的原則：嚴格依照提案命運分析的標記

| 分析中的標記 | 你的結論必須寫 | Action Items |
|---|---|---|
| ✅ 被採納 | 「採納此方案，具體做法是...」 | ✅ 列入 |
| ❌ 被放棄 | 「此方案被放棄，原因是...」 | ❌ 絕不列入 |
| ⏳ 待確認 | 「尚未定案，需要...之後才能決定」 | ❌ 不列入（可列為「待確認項目」） |

**如果你發現自己要把一個 ❌ 方案寫成結論或 Action Item — 停下來，你一定是搞錯了。**

## 輸出格式

### 會議紀錄：[用一句話概括會議核心主題]

#### 一、討論主題

**[編號]. [議題標題]**

- **問題/背景：** 為什麼要討論這個
- **方案/構想：** 提出了什麼解決方案（如有多個方案，分別說明）
- **爭議點：** 討論中的分歧或技術難點（若無則省略）
- **結論：** 最終決定是什麼。被放棄的方案要明確寫出「此方案被放棄，原因是...」。被採納的要寫清楚具體做法。

#### 二、最終結論與待辦事項（Action Items）

用條列式清楚列出：
- **嚴格只列出 ✅ 被採納的決議**
- 每條要具體（例如：「get devices API 逾時時改從 CP Topology 撈取快照回傳」）
- 如果有跨部門確認需求，標註出來
- 如果有「寫在 story 裡」「下個 sprint 做」等安排，要寫出來
- 被放棄和待確認的項目，可以在 Action Items 之後用「備註」或「待確認項目」的子區塊列出，但不能混入正式 Action Items

## 寫作原則
- 不要編造逐字稿中沒有的資訊
- 不要省略技術細節、數字、參數、具體方案名稱
- 每一支被討論的 API 都要獨立提及其結論
- 被放棄的方案也要記錄（說明曾經討論過、為什麼放棄），這對讀者理解決策脈絡很重要
- 寧可寫長一點也不要遺漏重要資訊

## 最後兩行
在摘要最末尾，獨立輸出以下兩行（各自獨佔一行）：
KEY_POINTS: [用逗號分隔的 3-8 個關鍵詞或短語]
TAGS: [用逗號分隔的 2-5 個分類標籤，例如：技術討論, API設計, 設備管理, 架構決策]

標籤的原則：
- 使用簡短的分類詞（2-6 字），方便日後搜尋篩選
- 反映會議的主題領域，而非具體技術細節
- 使用與逐字稿相同的語言"""


def _call_api(client, model, messages, progress_callback=None, phase_label=""):
    """呼叫 OpenAI API，含重試邏輯。"""
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=8192,
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
    """兩階段摘要：先分析提案命運，再撰寫正式會議紀錄。"""
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    model = config.LLM_MODEL

    # 組合參與者資訊
    participant_note = ""
    if participants:
        names = "、".join(participants)
        participant_note = f"\n\n【參考資訊】本次會議參與者：{names}\n（請在摘要中盡可能辨識發言者，如果逐字稿中能對應到的話）"

    # ── 第一階段：分析提案命運 ──
    if progress_callback:
        progress_callback("【階段 1/2】正在分析每個提案的命運...")

    analysis = _call_api(
        client, model,
        messages=[
            {"role": "system", "content": PHASE1_SYSTEM_PROMPT},
            {"role": "user", "content": f"以下是會議逐字稿，請按時間軸追蹤每個提案的命運：{participant_note}\n\n{transcript}"},
        ],
        progress_callback=progress_callback,
        phase_label="【階段 1】",
    )

    # ── 第二階段：根據分析撰寫正式摘要 ──
    if progress_callback:
        progress_callback("【階段 2/2】正在根據分析撰寫正式摘要...")

    content = _call_api(
        client, model,
        messages=[
            {"role": "system", "content": PHASE2_SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"以下是第一階段的「提案命運分析」：\n\n{analysis}\n\n"
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
