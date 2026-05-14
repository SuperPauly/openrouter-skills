"""
Parity tests for openrouter-images Python scripts.
Uses fixture API payloads — no network required.
"""

import sys
import os
import json
import base64
import importlib
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

import lib


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FAKE_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02"
    b"\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
    b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)
FAKE_PNG_B64 = base64.b64encode(FAKE_PNG_BYTES).decode("ascii")
FAKE_DATA_URL = f"data:image/png;base64,{FAKE_PNG_B64}"


def _fake_post(api_key, body):
    """Simulate a successful image generation API response."""
    return {
        "choices": [
            {
                "message": {
                    "content": "Here is your image.",
                    "images": [FAKE_DATA_URL],
                }
            }
        ]
    }


def _fake_post_no_images(api_key, body):
    return {"choices": [{"message": {"content": "No image for you.", "images": []}}]}


def _fake_post_multi(api_key, body):
    return {
        "choices": [
            {
                "message": {
                    "content": None,
                    "images": [FAKE_DATA_URL, FAKE_DATA_URL],
                }
            }
        ]
    }


# ---------------------------------------------------------------------------
# lib.py tests
# ---------------------------------------------------------------------------

class TestImagesLib(unittest.TestCase):
    def test_require_api_key_exits_when_absent(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OPENROUTER_API_KEY", None)
            with self.assertRaises(SystemExit) as ctx:
                lib.require_api_key()
        self.assertEqual(ctx.exception.code, 1)

    def test_require_api_key_returns_value(self):
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-test"}):
            key = lib.require_api_key()
        self.assertEqual(key, "sk-test")

    def test_default_output_path_format(self):
        path = lib.default_output_path()
        self.assertTrue(path.startswith("image-"))
        self.assertTrue(path.endswith(".png"))

    def test_save_and_read_image(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "test.png")
            saved = lib.save_image(FAKE_DATA_URL, out_path)
            self.assertEqual(saved, str(Path(out_path).resolve()))
            self.assertTrue(Path(saved).exists())
            content = Path(saved).read_bytes()
            self.assertEqual(content, FAKE_PNG_BYTES)

    def test_save_image_invalid_data_url_exits(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(SystemExit):
                lib.save_image("not-a-data-url", os.path.join(tmpdir, "out.png"))

    def test_read_image_as_data_url(self):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(FAKE_PNG_BYTES)
            tmp_path = f.name
        try:
            data_url = lib.read_image_as_data_url(tmp_path)
            self.assertTrue(data_url.startswith("data:image/png;base64,"))
            b64_part = data_url.split(",", 1)[1]
            self.assertEqual(base64.b64decode(b64_part), FAKE_PNG_BYTES)
        finally:
            os.unlink(tmp_path)

    def test_read_image_unsupported_extension_exits(self):
        with tempfile.NamedTemporaryFile(suffix=".bmp", delete=False) as f:
            f.write(b"BM")
            tmp_path = f.name
        try:
            with self.assertRaises(SystemExit) as ctx:
                lib.read_image_as_data_url(tmp_path)
            self.assertEqual(ctx.exception.code, 1)
        finally:
            os.unlink(tmp_path)

    def test_parse_args_positional_and_flags(self):
        result = lib.parse_args(["my prompt", "--model", "foo/bar", "--output", "out.png"])
        self.assertEqual(result["_0"], "my prompt")
        self.assertEqual(result["model"], "foo/bar")
        self.assertEqual(result["output"], "out.png")

    def test_parse_args_aspect_ratio_hyphen(self):
        result = lib.parse_args(["--aspect-ratio", "16:9"])
        self.assertEqual(result["aspect-ratio"], "16:9")


# ---------------------------------------------------------------------------
# generate.py tests
# ---------------------------------------------------------------------------

class TestGenerate(unittest.TestCase):
    def _run(self, argv, api_key="sk-test", post_impl=None):
        post_impl = post_impl or _fake_post
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "out.png")
            full_argv = argv[:]
            if "--output" not in full_argv:
                full_argv += ["--output", out_path]
            with patch.object(lib, "post_chat_completion", side_effect=post_impl), \
                 patch.dict(os.environ, {"OPENROUTER_API_KEY": api_key}), \
                 patch("sys.argv", ["generate.py"] + full_argv):
                import generate
                from importlib import reload
                import io
                buf = io.StringIO()
                with patch("sys.stdout", buf):
                    reload(generate)
                result = json.loads(buf.getvalue())
                return result, tmpdir

    def test_output_json_shape(self):
        result, _ = self._run(["a red panda"])
        self.assertIn("model", result)
        self.assertIn("prompt", result)
        self.assertIn("images_saved", result)
        self.assertIn("count", result)

    def test_prompt_preserved_in_output(self):
        result, _ = self._run(["a red panda"])
        self.assertEqual(result["prompt"], "a red panda")

    def test_default_model_used(self):
        result, _ = self._run(["a red panda"])
        self.assertEqual(result["model"], lib.DEFAULT_MODEL)

    def test_custom_model_used(self):
        result, _ = self._run(["a red panda", "--model", "custom/model"])
        self.assertEqual(result["model"], "custom/model")

    def test_single_image_saved(self):
        result, tmpdir = self._run(["a red panda"])
        self.assertEqual(result["count"], 1)
        self.assertEqual(len(result["images_saved"]), 1)
        self.assertTrue(Path(result["images_saved"][0]).exists())

    def test_multi_image_naming(self):
        """When API returns 2 images, names are base-1.png, base-2.png."""
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "out.png")
            with patch.object(lib, "post_chat_completion", side_effect=_fake_post_multi), \
                 patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-test"}), \
                 patch("sys.argv", ["generate.py", "prompt", "--output", out_path]):
                import generate
                from importlib import reload
                import io
                buf = io.StringIO()
                with patch("sys.stdout", buf):
                    reload(generate)
                result = json.loads(buf.getvalue())
            self.assertEqual(result["count"], 2)
            for path in result["images_saved"]:
                self.assertTrue(Path(path).exists())

    def test_no_images_exits_with_1(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "out.png")
            with patch.object(lib, "post_chat_completion", side_effect=_fake_post_no_images), \
                 patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-test"}), \
                 patch("sys.argv", ["generate.py", "prompt", "--output", out_path]):
                import generate
                from importlib import reload
                with self.assertRaises(SystemExit) as ctx:
                    reload(generate)
                self.assertEqual(ctx.exception.code, 1)

    def test_missing_prompt_exits_with_1(self):
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-test"}), \
             patch("sys.argv", ["generate.py"]):
            import generate
            from importlib import reload
            with self.assertRaises(SystemExit) as ctx:
                reload(generate)
            self.assertEqual(ctx.exception.code, 1)

    def test_missing_api_key_exits_with_1(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OPENROUTER_API_KEY", None)
            with patch("sys.argv", ["generate.py", "a prompt"]):
                import generate
                from importlib import reload
                with self.assertRaises(SystemExit) as ctx:
                    reload(generate)
                self.assertEqual(ctx.exception.code, 1)

    def test_aspect_ratio_and_image_size_flags_accepted(self):
        result, _ = self._run(["a red panda", "--aspect-ratio", "16:9", "--image-size", "1K"])
        self.assertIn("images_saved", result)


# ---------------------------------------------------------------------------
# edit.py tests
# ---------------------------------------------------------------------------

class TestEdit(unittest.TestCase):
    def _make_image_file(self, tmpdir, ext=".png"):
        p = Path(tmpdir) / f"source{ext}"
        p.write_bytes(FAKE_PNG_BYTES)
        return str(p)

    def _run(self, argv, api_key="sk-test", post_impl=None):
        post_impl = post_impl or _fake_post
        with tempfile.TemporaryDirectory() as tmpdir:
            img = self._make_image_file(tmpdir)
            out_path = os.path.join(tmpdir, "out.png")
            full_argv = [img] + argv
            if "--output" not in full_argv:
                full_argv += ["--output", out_path]
            with patch.object(lib, "post_chat_completion", side_effect=post_impl), \
                 patch.dict(os.environ, {"OPENROUTER_API_KEY": api_key}), \
                 patch("sys.argv", ["edit.py"] + full_argv):
                import edit
                from importlib import reload
                import io
                buf = io.StringIO()
                with patch("sys.stdout", buf):
                    reload(edit)
                result = json.loads(buf.getvalue())
                return result

    def test_output_json_shape(self):
        result = self._run(["make it look like a painting"])
        self.assertIn("model", result)
        self.assertIn("source_image", result)
        self.assertIn("prompt", result)
        self.assertIn("images_saved", result)
        self.assertIn("count", result)

    def test_prompt_and_source_preserved(self):
        result = self._run(["make it look like a painting"])
        self.assertEqual(result["prompt"], "make it look like a painting")
        self.assertIn("source", result["source_image"])

    def test_default_model_used(self):
        result = self._run(["transform it"])
        self.assertEqual(result["model"], lib.DEFAULT_MODEL)

    def test_custom_model_used(self):
        result = self._run(["transform it", "--model", "custom/img-model"])
        self.assertEqual(result["model"], "custom/img-model")

    def test_saved_file_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            img = self._make_image_file(tmpdir)
            out_path = os.path.join(tmpdir, "edited.png")
            with patch.object(lib, "post_chat_completion", side_effect=_fake_post), \
                 patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-test"}), \
                 patch("sys.argv", ["edit.py", img, "make it blue", "--output", out_path]):
                import edit
                from importlib import reload
                import io
                buf = io.StringIO()
                with patch("sys.stdout", buf):
                    reload(edit)
                result = json.loads(buf.getvalue())
            self.assertTrue(Path(result["images_saved"][0]).exists())

    def test_missing_prompt_exits_with_1(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            img = self._make_image_file(tmpdir)
            with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-test"}), \
                 patch("sys.argv", ["edit.py", img]):
                import edit
                from importlib import reload
                with self.assertRaises(SystemExit) as ctx:
                    reload(edit)
                self.assertEqual(ctx.exception.code, 1)

    def test_missing_api_key_exits_with_1(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            img = self._make_image_file(tmpdir)
            with patch.dict(os.environ, {}, clear=True):
                os.environ.pop("OPENROUTER_API_KEY", None)
                with patch("sys.argv", ["edit.py", img, "make it blue"]):
                    import edit
                    from importlib import reload
                    with self.assertRaises(SystemExit) as ctx:
                        reload(edit)
                    self.assertEqual(ctx.exception.code, 1)

    def test_unsupported_image_format_exits_with_1(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_img = Path(tmpdir) / "bad.bmp"
            bad_img.write_bytes(b"BM")
            with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-test"}), \
                 patch("sys.argv", ["edit.py", str(bad_img), "make it blue"]):
                import edit
                from importlib import reload
                with self.assertRaises(SystemExit) as ctx:
                    reload(edit)
                self.assertEqual(ctx.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
