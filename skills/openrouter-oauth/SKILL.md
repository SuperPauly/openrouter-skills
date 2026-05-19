---
name: openrouter-oauth
description: Implement Sign In with OpenRouter using OAuth PKCE and Python server callbacks. Use when adding OpenRouter login, API-key exchange, or per-user OpenRouter keys.
version: 2.0.0
compatibility: Python web apps
---

# Sign In with OpenRouter

Add OpenRouter login to a Python web app. Users authorize on OpenRouter and your app exchanges the authorization code for an API key.

## Flow

1. Generate a `code_verifier` with secure random bytes.
2. Store the verifier in the user's signed server session.
3. Redirect the user to OpenRouter with the S256 challenge.
4. Receive the callback with `code`.
5. Exchange `code` and `code_verifier` for an OpenRouter API key.
6. Store the key in your encrypted user secrets table.

## PKCE Helpers

```python
from __future__ import annotations

import base64
import hashlib
import secrets

def base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")

def generate_code_verifier() -> str:
    return base64url(secrets.token_bytes(32))

def compute_s256_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64url(digest)
```

## Flask Example

```python
from urllib.parse import urlencode

import requests
from flask import Flask, redirect, request, session, url_for

app = Flask(__name__)
app.secret_key = "replace-with-a-secure-secret"

OPENROUTER_AUTH_URL = "https://openrouter.ai/auth"
OPENROUTER_KEYS_URL = "https://openrouter.ai/api/v1/auth/keys"

@app.get("/auth/openrouter/start")
def start_openrouter_auth():
    verifier = generate_code_verifier()
    session["openrouter_code_verifier"] = verifier
    callback_url = url_for("finish_openrouter_auth", _external=True)
    params = {
        "callback_url": callback_url,
        "code_challenge": compute_s256_challenge(verifier),
        "code_challenge_method": "S256",
    }
    return redirect(f"{OPENROUTER_AUTH_URL}?{urlencode(params)}")

@app.get("/auth/openrouter/callback")
def finish_openrouter_auth():
    code = request.args.get("code")
    verifier = session.pop("openrouter_code_verifier", None)
    if not code or not verifier:
        return "Missing OpenRouter OAuth state", 400
    response = requests.post(
        OPENROUTER_KEYS_URL,
        json={"code": code, "code_verifier": verifier, "code_challenge_method": "S256"},
        timeout=30,
    )
    response.raise_for_status()
    api_key = response.json()["key"]
    save_user_openrouter_key(user_id=current_user_id(), api_key=api_key)
    return redirect("/settings?openrouter=connected")
```

## FastAPI Example

```python
from urllib.parse import urlencode

import requests
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse

app = FastAPI()

@app.get("/auth/openrouter/start")
def start(request: Request):
    verifier = generate_code_verifier()
    request.session["openrouter_code_verifier"] = verifier
    callback_url = str(request.url_for("finish"))
    params = {
        "callback_url": callback_url,
        "code_challenge": compute_s256_challenge(verifier),
        "code_challenge_method": "S256",
    }
    return RedirectResponse(f"https://openrouter.ai/auth?{urlencode(params)}")

@app.get("/auth/openrouter/callback")
def finish(request: Request, code: str | None = None):
    verifier = request.session.pop("openrouter_code_verifier", None)
    if not code or not verifier:
        raise HTTPException(status_code=400, detail="Missing OpenRouter OAuth state")
    response = requests.post(
        "https://openrouter.ai/api/v1/auth/keys",
        json={"code": code, "code_verifier": verifier, "code_challenge_method": "S256"},
        timeout=30,
    )
    response.raise_for_status()
    save_user_openrouter_key(user_id=current_user_id(), api_key=response.json()["key"])
    return RedirectResponse("/settings?openrouter=connected")
```

## Using the User Key

```python
import requests

def call_openrouter_for_user(user_id: str, message: str) -> str:
    api_key = load_user_openrouter_key(user_id)
    response = requests.post(
        "https://openrouter.ai/api/v1/responses",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "openai/gpt-4o-mini", "input": message},
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data["output"][0]["content"][0]["text"]
```

## Security Notes

- Keep the verifier in a signed server session.
- Do not place the resulting API key in browser storage.
- Encrypt stored user API keys at rest.
- Remove the verifier from the session after the callback.
- Validate that the callback belongs to a pending login attempt before exchanging the code.
