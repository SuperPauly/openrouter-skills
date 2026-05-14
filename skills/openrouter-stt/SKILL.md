---
name: openrouter-stt
description: Transcribe speech to text using OpenRouter's speech-to-text API. Use when the user asks to transcribe audio, convert speech to text, extract a transcript from a recording or meeting, caption a video's audio, or mentions STT, speech-to-text, ASR, or transcription.
---

# OpenRouter Speech-to-Text

Transcribe audio via `POST /api/v1/audio/transcriptions` using `curl`. Requires `OPENROUTER_API_KEY` (get one at https://openrouter.ai/keys). If unset, stop and ask.

**This endpoint is not OpenAI-compatible.** The body is JSON with base64 audio under `input_audio: { data, format }` — not `multipart/form-data` with a `file` field the way OpenAI's `/v1/audio/transcriptions` works. Do not point the OpenAI SDK at this endpoint; it will send the wrong shape. Use `curl`, `fetch`, or `requests` directly.

## One call, JSON back

Both request and response are JSON. The response body carries:

- `text` — the transcript.
- `usage` — always includes `cost`. Providers additionally report either `seconds` of audio billed or a token breakdown (`total_tokens`, `input_tokens`, `output_tokens`), depending on how they price the request. Don't assume both are present.

Sample response (duration-priced provider, e.g. `google/chirp-3`):

```json
{
  "text": "I used to rule the world.",
  "usage": {
    "seconds": 20,
    "cost": 0.005333
  }
}
```

Sample response (token-priced provider):

```json
{
  "text": "Hello, this is a test of speech-to-text transcription.",
  "usage": {
    "total_tokens": 113,
    "input_tokens": 83,
    "output_tokens": 30,
    "cost": 0.000508
  }
}
```

## Drop-in workflow

```bash
#!/usr/bin/env bash
set -euo pipefail

MODEL="google/chirp-3"
FORMAT="wav"                          # wav, mp3, flac, m4a, ogg, webm, aac
AUDIO="audio.wav"
BODY=$(mktemp)
PAYLOAD=$(mktemp)

audio_b64=$(base64 < "$AUDIO" | tr -d '\n')

jq -n --arg model "$MODEL" --arg data "$audio_b64" --arg fmt "$FORMAT" \
  '{model: $model, input_audio: {data: $data, format: $fmt}}' > "$PAYLOAD"

# --data-binary @file keeps the base64 payload off argv (avoids E2BIG / ARG_MAX).
http_code=$(curl -sS -X POST https://openrouter.ai/api/v1/audio/transcriptions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  --output "$BODY" \
  -w '%{http_code}' \
  --data-binary @"$PAYLOAD")

if [[ "$http_code" != "200" ]]; then
  echo "STT failed (HTTP $http_code):" >&2
  cat "$BODY" >&2
  rm -f "$BODY" "$PAYLOAD"
  exit 1
fi

jq -r '.text' "$BODY"
rm -f "$BODY" "$PAYLOAD"
```

## Discovering STT models

Filter the models endpoint by output modality to list transcription models.

```bash
curl -sS "https://openrouter.ai/api/v1/models?output_modalities=transcription" \
  | jq '.data[] | {id, name, pricing}'
```

Models are provider-namespaced — use the full slug (`google/chirp-3`, `openai/whisper-1`, `openai/whisper-large-v3`), not the short name.

## Parameters

| Field                | Required | Notes                                                                                                     |
| -------------------- | -------- | --------------------------------------------------------------------------------------------------------- |
| `model`              | yes      | Full model slug from `/api/v1/models?output_modalities=transcription`.                                    |
| `input_audio.data`   | yes      | Base64-encoded raw audio bytes. **Not** a data URI — just the base64 payload, no `data:audio/...;base64,` prefix. |
| `input_audio.format` | yes      | `wav`, `mp3`, `flac`, `m4a`, `ogg`, `webm`, or `aac`. Must match the actual bytes. Support varies by provider. |
| `language`           | no       | ISO-639-1 code (`en`, `ja`, `fr`). Auto-detected if omitted.                                              |
| `temperature`        | no       | 0–1. Lower is more deterministic.                                                                         |
| `provider`           | no       | Provider passthrough — see below.                                                                         |

### Picking an audio format

- **`wav`** / **`flac`** — uncompressed or lossless. Highest quality; largest uploads.
- **`mp3`** / **`m4a`** / **`aac`** — compressed. Smaller payloads, which matters because base64 inflates bytes by ~33% on top of whatever the file already weighs.
- **`webm`** / **`ogg`** — typical for browser recordings (`MediaRecorder`).

The `format` field must match the actual container/codec of the bytes. A file saved as `.wav` that is actually mp3 will be rejected or mis-decoded. When in doubt, confirm with `ffprobe <file>`.

## Provider-specific options

Provider passthrough goes under `provider.options.<slug>` and is only forwarded when that provider handles the request. Example — Groq's `prompt` for vocabulary hinting:

```json
{
  "model": "openai/whisper-large-v3",
  "input_audio": { "data": "UklGRiQA...", "format": "wav" },
  "provider": {
    "options": {
      "groq": {
        "prompt": "Expected vocabulary: OpenRouter, API, transcription"
      }
    }
  }
}
```

Options keyed by provider slug are forwarded only when that provider matches; other keys are ignored. Check each provider's upstream docs for available passthrough keys.

## Python (urllib)

```python
import base64
import json
import os
from urllib import request, error

with open("audio.wav", "rb") as f:
    audio = f.read()

payload = json.dumps(
    {
        "model": "google/chirp-3",
        "input_audio": {"data": base64.b64encode(audio).decode("ascii"), "format": "wav"},
    }
).encode("utf-8")

req = request.Request(
    "https://openrouter.ai/api/v1/audio/transcriptions",
    data=payload,
    headers={
        "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
        "Content-Type": "application/json",
    },
    method="POST",
)

try:
    with request.urlopen(req) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    print(result.get("text", ""))
except error.HTTPError as e:
    body = e.read().decode("utf-8", errors="replace")
    raise RuntimeError(f"STT failed (HTTP {e.code}): {body}")
```

## Python (requests)

Drop-in script — reads audio from a file path argument or stdin, prints transcript to stdout, prints cost info to stderr.

```python
#!/usr/bin/env python3
"""OpenRouter STT drop-in: python stt.py <audio_file> [--model <model>]"""
import argparse
import json
import sys
import requests

BASE_URL = "https://openrouter.ai/api/v1"


def transcribe(audio_path: str, model: str, api_key: str) -> dict:
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    import base64
    audio_b64 = base64.b64encode(audio_bytes).decode()
    ext = audio_path.rsplit(".", 1)[-1].lower()
    mime = {
        "mp3": "audio/mpeg", "wav": "audio/wav", "ogg": "audio/ogg",
        "flac": "audio/flac", "m4a": "audio/mp4", "webm": "audio/webm",
    }.get(ext, "audio/mpeg")

    resp = requests.post(
        f"{BASE_URL}/responses",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "input": [{
                "role": "user",
                "content": [
                    {"type": "input_audio", "data": audio_b64, "mime_type": mime},
                    {"type": "input_text", "text": "Transcribe the audio. Return only the transcript text, nothing else."},
                ],
            }],
        },
    )
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    parser = argparse.ArgumentParser(description="Transcribe audio via OpenRouter STT")
    parser.add_argument("audio_file", help="Path to audio file")
    parser.add_argument("--model", default="openai/whisper-large-v3", help="STT model slug")
    parser.add_argument("--api-key", help="OpenRouter API key (or set OPENROUTER_API_KEY)")
    args = parser.parse_args()

    import os
    api_key = args.api_key or os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    data = transcribe(args.audio_file, args.model, api_key)

    transcript = ""
    for item in data.get("output", []):
        if item.get("type") == "message":
            for part in item.get("content", []):
                if part.get("type") == "output_text":
                    transcript += part["text"]

    print(transcript)

    usage = data.get("usage", {})
    in_t = usage.get("input_tokens", 0)
    out_t = usage.get("output_tokens", 0)
    print(f"[tokens: {in_t} in / {out_t} out]", file=sys.stderr)


if __name__ == "__main__":
    main()
```

Usage:
```bash
python stt.py recording.mp3
python stt.py recording.wav --model openai/whisper-large-v3
OPENROUTER_API_KEY=sk-or-... python stt.py audio.flac
```

## Troubleshooting

**Garbled or empty `text`** — the `format` field probably doesn't match the actual bytes, or the audio is silent/corrupted. Confirm with `ffprobe audio.wav`.

**400 with `"Invalid base64"` or silent failure** — `data` must be just base64, not a data URI (`data:audio/wav;base64,...`). Strip the prefix if you copied it from a browser `FileReader`.

**400 with a `ZodError`** — a required field is missing or the wrong type. The body looks like `{"success":false,"error":{"name":"ZodError","message":"[...]"}}` — the nested `message` JSON string names the bad path (commonly `input_audio.data` or `input_audio.format`).

**413 / request too large** — base64 inflates bytes by ~33%, so a large raw file becomes an even larger JSON payload. Use a smaller source file (compressed format, lower sample rate, or trimmed clip).

**Model not found** — use the full slug from `/api/v1/models?output_modalities=transcription` (`google/chirp-3`, not `chirp-3`).

## References

- [STT guide](https://openrouter.ai/docs/guides/overview/multimodal/stt)
- [Models page — filter to transcription output](https://openrouter.ai/models?output_modalities=transcription)
