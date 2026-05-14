"""
Tests for run_agent_with_retry semantics.
Python equivalent of test/retry.test.ts
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def make_runtime_error(status: int) -> RuntimeError:
    return RuntimeError(f"API error {status}: HTTP {status}")


def run_with_retry(runner, *, on_event=None, max_retries: int = 3) -> dict:
    """
    Standalone reimplementation of run_agent_with_retry logic for testing.
    Mirrors the production implementation in src/agent.py.
    """
    for attempt in range(max_retries + 1):
        tool_calls_made = 0

        def tracking_on_event(event):
            nonlocal tool_calls_made
            if event.get("type") == "tool_call":
                tool_calls_made += 1
            if on_event:
                on_event(event)

        try:
            return runner(tracking_on_event)
        except RuntimeError as e:
            msg = str(e)
            status = None
            if msg.startswith("API error "):
                try:
                    status = int(msg.split()[2].rstrip(":"))
                except (IndexError, ValueError):
                    pass
            retryable = status == 429 or (status is not None and 500 <= status < 600)
            if not retryable or attempt == max_retries or tool_calls_made > 0:
                raise
            # No sleep in tests


class TestRunAgentWithRetry:
    def test_retries_on_429_before_tool_calls_and_eventually_succeeds(self):
        calls = [0]

        def runner(on_event):
            calls[0] += 1
            if calls[0] < 3:
                raise make_runtime_error(429)
            return {"text": "ok"}

        result = run_with_retry(runner)
        assert calls[0] == 3
        assert result["text"] == "ok"

    def test_retries_on_500_before_tool_calls(self):
        calls = [0]

        def runner(on_event):
            calls[0] += 1
            if calls[0] < 2:
                raise make_runtime_error(500)
            return {"text": "ok"}

        result = run_with_retry(runner)
        assert calls[0] == 2

    def test_does_not_retry_after_tool_call(self):
        calls = [0]

        def runner(on_event):
            calls[0] += 1
            on_event({"type": "tool_call", "name": "file_write", "callId": "c1", "args": {}})
            raise make_runtime_error(500)

        with pytest.raises(RuntimeError, match="500"):
            run_with_retry(runner)
        assert calls[0] == 1

    def test_does_not_retry_non_retryable_errors(self):
        for status in [400, 401, 403, 404]:
            calls = [0]

            def runner(on_event, _s=status):
                calls[0] += 1
                raise make_runtime_error(_s)

            with pytest.raises(RuntimeError, match=str(status)):
                run_with_retry(runner)
            assert calls[0] == 1

    def test_gives_up_after_max_retries(self):
        calls = [0]

        def runner(on_event):
            calls[0] += 1
            raise make_runtime_error(429)

        with pytest.raises(RuntimeError, match="429"):
            run_with_retry(runner, max_retries=2)
        assert calls[0] == 3  # initial + 2 retries

    def test_per_attempt_tool_counter_resets(self):
        calls = [0]

        def runner(on_event):
            calls[0] += 1
            if calls[0] == 1:
                raise make_runtime_error(500)
            on_event({"type": "tool_call", "name": "shell", "callId": "c1", "args": {}})
            return {"text": "done"}

        result = run_with_retry(runner)
        assert calls[0] == 2
        assert result["text"] == "done"
