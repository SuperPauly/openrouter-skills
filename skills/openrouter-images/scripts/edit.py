#!/usr/bin/env python3
"""
Edit an existing image with a text prompt.

Usage: python edit.py <image-path> "prompt" [--model <id>] [--output <path>] [--aspect-ratio <r>] [--image-size <s>]

Examples:
  python edit.py photo.jpg "make it look like a painting"
  python edit.py input.png "add a rainbow" --output output.png
"""
import sys
import json
import os
from lib import (
    DEFAULT_MODEL,
    require_api_key,
    parse_args,
    post_chat_completion,
    read_image_as_data_url,
    save_image,
    default_output_path,
)

sys.path.insert(0, os.path.dirname(__file__))

api_key = require_api_key()
args = parse_args(sys.argv[1:])

image_path = args.get("_0")
prompt = args.get("_1")

if not image_path or not prompt:
    print(
        'Usage: python edit.py <image-path> "prompt" [--model <id>] [--output <path>] [--aspect-ratio <r>] [--image-size <s>]',
        file=sys.stderr,
    )
    sys.exit(1)

model = args.get("model") or DEFAULT_MODEL
output_base = args.get("output") or default_output_path()
aspect_ratio = args.get("aspect-ratio")
image_size = args.get("image-size")

data_url = read_image_as_data_url(str(image_path))

image_config: dict = {}
if aspect_ratio:
    image_config["aspect_ratio"] = aspect_ratio
if image_size:
    image_config["image_size"] = image_size

body: dict = {
    "model": model,
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": data_url}},
                {"type": "text", "text": prompt},
            ],
        }
    ],
    "modalities": ["image", "text"],
}
if image_config:
    body["image_config"] = image_config

result = post_chat_completion(api_key, body)
message = (result.get("choices") or [{}])[0].get("message")

if not message:
    print("Error: No response from model.", file=sys.stderr)
    sys.exit(1)

if message.get("content"):
    print(f"Model: {message['content']}", file=sys.stderr)

images: list = message.get("images") or []
if not images:
    print("Error: No images returned by model.", file=sys.stderr)
    sys.exit(1)

saved: list[str] = []
for i, img in enumerate(images):
    data_url_out = img if img.startswith("data:") else f"data:image/png;base64,{img}"
    if len(images) == 1:
        out_path = output_base
    else:
        base, _, ext = output_base.rpartition(".")
        if base:
            out_path = f"{base}-{i + 1}.{ext}"
        else:
            out_path = f"{output_base}-{i + 1}.png"
    abs_path = save_image(data_url_out, out_path)
    saved.append(abs_path)

print(json.dumps(
    {"model": model, "source_image": image_path, "prompt": prompt, "images_saved": saved, "count": len(saved)},
    indent=2,
))
