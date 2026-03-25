import io
import json
import os
import subprocess
import time
import tempfile
from pathlib import Path
from openai import OpenAI
import config


def _get_ffmpeg_path():
    """取得 ffmpeg 執行檔路徑。"""
    # 優先用系統 PATH 裡的 ffmpeg
    import shutil
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return sys_ffmpeg

    # 使用 imageio-ffmpeg 提供的
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        pass

    raise RuntimeError(
        "找不到 ffmpeg。\n"
        "安裝方式：pip install imageio-ffmpeg\n"
        "或 Windows: winget install Gyan.FFmpeg"
    )


def transcribe(audio_path: str, progress_callback=None) -> dict:
    """
    使用 Whisper API 轉錄音檔。
    回傳 dict: {'raw_text': 帶時間戳逐字稿, 'segments': 片段列表}
    """
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    model = config.WHISPER_MODEL

    file_path = Path(audio_path)
    file_size_mb = file_path.stat().st_size / (1024 * 1024)

    if file_size_mb <= config.MAX_AUDIO_SIZE_MB:
        if progress_callback:
            progress_callback("正在轉錄語音...")
        return _transcribe_file(client, model, file_path)
    else:
        if progress_callback:
            progress_callback(
                f"檔案 {file_size_mb:.1f} MB 超過 {config.MAX_AUDIO_SIZE_MB} MB 限制，正在分段處理..."
            )
        return _transcribe_large_file(client, model, file_path, progress_callback)


def _transcribe_file(client, model, file_path, max_retries=3):
    """轉錄單一檔案，含重試邏輯。"""
    for attempt in range(max_retries):
        try:
            with open(file_path, "rb") as f:
                response = client.audio.transcriptions.create(
                    model=model,
                    file=f,
                    response_format="verbose_json",
                )

            segments = []
            lines = []

            # 解析 segments（處理 dict 和 object 兩種格式）
            raw_segments = _get_attr(response, 'segments', [])
            if raw_segments:
                for seg in raw_segments:
                    start = _format_time(_get_attr(seg, 'start', 0))
                    end = _format_time(_get_attr(seg, 'end', 0))
                    text = str(_get_attr(seg, 'text', '')).strip()

                    if text:
                        segments.append({
                            'start': start,
                            'end': end,
                            'text': text,
                        })
                        lines.append(f"[{start} → {end}] {text}")
            else:
                # 沒有 segments，使用完整文字
                text = str(_get_attr(response, 'text', response))
                lines.append(text)
                segments.append({
                    'start': '00:00:00',
                    'end': '00:00:00',
                    'text': text,
                })

            return {
                'raw_text': '\n'.join(lines),
                'segments': segments,
            }

        except Exception as e:
            error_str = str(e).lower()
            if "rate_limit" in error_str or "429" in error_str:
                wait = (attempt + 1) * 10
            elif attempt < max_retries - 1:
                wait = (attempt + 1) * 3
            else:
                raise RuntimeError(f"轉錄失敗（重試 {max_retries} 次）：{str(e)}")
            time.sleep(wait)

    raise RuntimeError("轉錄失敗：API 速率限制，請稍後再試")


def _transcribe_large_file(client, model, file_path, progress_callback=None):
    """分段轉錄大檔案，使用 ffmpeg 直接分段。"""
    ffmpeg = _get_ffmpeg_path()

    # 取得音檔時長（秒）
    duration = _get_duration(ffmpeg, str(file_path))
    if duration <= 0:
        raise RuntimeError("無法取得音檔時長，檔案可能損毀。")

    # 每段目標 20MB 對應約多長？先壓一小段 sample 估算
    sample_duration = min(30, duration)  # 取 30 秒 sample
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        sample_path = tmp.name
    _ffmpeg_extract(ffmpeg, str(file_path), sample_path, 0, sample_duration)
    sample_size = os.path.getsize(sample_path)
    os.unlink(sample_path)

    bytes_per_second = sample_size / max(sample_duration, 1)
    target_bytes = config.MAX_AUDIO_SIZE_MB * 0.8 * 1024 * 1024  # 20MB
    chunk_seconds = int(target_bytes / max(bytes_per_second, 1))
    chunk_seconds = max(chunk_seconds, 60)  # 至少 60 秒一段

    # 切段
    chunks = []
    offset = 0
    while offset < duration:
        end = min(offset + chunk_seconds, duration)
        chunks.append((offset, end))
        offset = end

    all_segments = []
    all_lines = []

    for i, (start_sec, end_sec) in enumerate(chunks):
        if progress_callback:
            progress_callback(f"轉錄中... 片段 {i + 1}/{len(chunks)}")

        # 用 ffmpeg 擷取這段並壓成 mp3
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            chunk_path = tmp.name
        _ffmpeg_extract(ffmpeg, str(file_path), chunk_path, start_sec, end_sec - start_sec)

        try:
            result = _transcribe_file(client, model, Path(chunk_path))
        finally:
            try:
                os.unlink(chunk_path)
            except OSError:
                pass

        # 用偏移量調整時間戳
        for seg in result['segments']:
            adj_start = _add_seconds_to_time(seg['start'], start_sec)
            adj_end = _add_seconds_to_time(seg['end'], start_sec)
            seg['start'] = adj_start
            seg['end'] = adj_end
            all_segments.append(seg)
            all_lines.append(f"[{adj_start} → {adj_end}] {seg['text']}")

    return {
        'raw_text': '\n'.join(all_lines),
        'segments': all_segments,
    }


def _get_duration(ffmpeg, file_path):
    """用 ffmpeg 取得音檔時長（秒）。"""
    cmd = [
        ffmpeg, '-i', file_path,
        '-f', 'null', '-hide_banner',
    ]
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=30,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
    )
    # ffmpeg 把資訊輸出到 stderr
    output = result.stderr
    # 找 Duration: HH:MM:SS.xx
    import re
    match = re.search(r'Duration:\s*(\d+):(\d+):(\d+)\.(\d+)', output)
    if match:
        h, m, s, cs = match.groups()
        return int(h) * 3600 + int(m) * 60 + int(s) + int(cs) / 100
    return 0


def _ffmpeg_extract(ffmpeg, input_path, output_path, start_sec, duration_sec):
    """用 ffmpeg 擷取音檔片段並壓成 mono mp3。"""
    cmd = [
        ffmpeg,
        '-y',  # 覆寫
        '-i', input_path,
        '-ss', str(start_sec),
        '-t', str(duration_sec),
        '-ac', '1',           # mono
        '-ar', '16000',       # 16kHz
        '-ab', '64k',         # 64kbps
        '-f', 'mp3',
        output_path,
    ]
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=120,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 轉檔失敗：{result.stderr[-500:]}")


def _get_attr(obj, key, default=None):
    """安全取值，同時處理 dict 和 object。"""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _format_time(seconds):
    """將秒數轉為 HH:MM:SS 格式。"""
    if isinstance(seconds, str):
        return seconds
    seconds = float(seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def _add_seconds_to_time(time_str, offset_seconds):
    """在 HH:MM:SS 時間字串上加上偏移秒數。"""
    parts = time_str.split(':')
    total = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2]) + offset_seconds
    return _format_time(total)
