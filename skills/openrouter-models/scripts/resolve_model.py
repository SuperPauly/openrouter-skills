#!/usr/bin/env python3
"""
Resolve an informal model name to an exact OpenRouter model ID.

Usage: python resolve_model.py <query>

Examples:
  python resolve_model.py "claude sonnet"
  python resolve_model.py "gpt 4o mini"
  python resolve_model.py "llama 3.1"
"""
import sys
import json
import re
from lib import optional_api_key, fetch_api, format_model, parse_args

STOP_WORDS = {"the", "a", "an", "model", "latest", "best", "from", "by", "most", "for"}


def tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"[\s\-_/:.]+", text.lower()) if t]


def remove_stop_words(tokens: list[str]) -> list[str]:
    return [t for t in tokens if t not in STOP_WORDS]


def collapse(text: str) -> str:
    return re.sub(r"[\s\-_/:.]+", "", text.lower())


def bigrams(text: str) -> set[str]:
    return {text[i:i+2] for i in range(len(text) - 1)}


def bigram_dice(a: str, b: str) -> float:
    ba = bigrams(a)
    bb = bigrams(b)
    if not ba and not bb:
        return 0.0
    intersection = len(ba & bb)
    return (2 * intersection) / (len(ba) + len(bb))


def strip_provider(model_id: str) -> str:
    slash = model_id.find("/")
    return model_id[slash + 1:] if slash >= 0 else model_id


def token_overlap_score(query_tokens: list[str], target_tokens: list[str]) -> float:
    if not query_tokens:
        return 0.0
    matched = 0
    last_index = -1
    order_bonus = 0
    for qt in query_tokens:
        idx = next(
            (i for i, tt in enumerate(target_tokens)
             if i > last_index - 1 and (tt == qt or qt in tt or tt in qt)),
            -1,
        )
        if idx >= 0:
            matched += 1
            if idx > last_index:
                order_bonus += 1
            last_index = idx
    overlap = matched / len(query_tokens)
    order_ratio = order_bonus / matched if matched > 0 else 0
    return overlap * (0.8 + 0.2 * order_ratio)


def substring_score(collapsed_query: str, model_id: str, model_name: str) -> float:
    if collapsed_query in collapse(model_id):
        return 1.0
    if collapsed_query in collapse(model_name):
        return 1.0
    return 0.0


def score_model(query_tokens: list[str], collapsed_query: str, m: dict) -> float:
    model_id = (m.get("id") or "").lower()
    model_name = (m.get("name") or "").lower()
    target_tokens = tokenize(f"{model_id} {model_name}")
    token_s = token_overlap_score(query_tokens, target_tokens)
    sub_s = substring_score(collapsed_query, model_id, model_name)
    stripped_id = strip_provider(model_id)
    bigram_s = max(
        bigram_dice(collapsed_query, collapse(stripped_id)),
        bigram_dice(collapsed_query, collapse(model_name)),
    )
    return token_s * 0.5 + sub_s * 0.3 + bigram_s * 0.2


def confidence(score: float) -> str:
    if score >= 0.85:
        return "high"
    if score >= 0.55:
        return "medium"
    return "low"


api_key = optional_api_key()
args = parse_args(sys.argv[1:])
raw_query = args.get("_0")

if not raw_query or not str(raw_query).strip():
    print(
        'Usage: python resolve_model.py <query>\n\n'
        'Resolves an informal model name to an exact OpenRouter model ID.\n\n'
        'Examples:\n'
        '  python resolve_model.py "claude sonnet"\n'
        '  python resolve_model.py "gpt 4o mini"\n'
        '  python resolve_model.py "llama 3.1"',
        file=sys.stderr,
    )
    sys.exit(1)

query = str(raw_query)
data = fetch_api("/models", api_key)
models = data.get("data") or []

# Exact ID match short-circuit
exact = next((m for m in models if (m.get("id") or "").lower() == query.lower()), None)
if exact:
    result = {**format_model(exact), "confidence": "high", "score": 1.0}
    print(json.dumps([result], indent=2))
    sys.exit(0)

query_tokens = remove_stop_words(tokenize(query))

if not query_tokens:
    print(
        'Query contains only stop words. Try a more specific model name.\n'
        'Examples: "claude sonnet", "gpt 4o", "llama 3.1"',
        file=sys.stderr,
    )
    print(json.dumps([]))
    sys.exit(0)

collapsed_query = collapse(" ".join(query_tokens))

scored = []
for m in models:
    s = score_model(query_tokens, collapsed_query, m)
    if s >= 0.3:
        scored.append((s, m))

scored.sort(key=lambda x: x[0], reverse=True)
scored = scored[:5]

if not scored:
    print(
        f'No models matched "{query}". Try a more specific name or use search_models.py for substring matching.',
        file=sys.stderr,
    )
    print(json.dumps([]))
    sys.exit(0)

output = [
    {**format_model(m), "confidence": confidence(s), "score": round(s, 2)}
    for s, m in scored
]
print(json.dumps(output, indent=2))
