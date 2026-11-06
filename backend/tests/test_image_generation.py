import asyncio
import base64
import json
import os
import unittest
from unittest.mock import AsyncMock, patch

import httpx

os.environ.setdefault("GROQ_API_KEY", "test-key")
import main
from core.image_generation import generate_image, ImageGenerationError
from core.router import router

JPEG = base64.b64encode(b"\xff\xd8\xfftest-image").decode()
IMAGE = {"data": JPEG, "mime_type": "image/jpeg", "prompt": "A robot", "model": "test-image-model"}


class ImageGenerationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {"IMAGE_GENERATION_ENABLED": "true", "OPENAI_API_KEY": "private-test-key"})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def client(self, handler):
        constructor = httpx.AsyncClient
        return patch("core.image_generation.httpx.AsyncClient", side_effect=lambda **kwargs:
                     constructor(transport=httpx.MockTransport(handler), **kwargs))

    def test_creation_intent_does_not_capture_image_discussion(self):
        for prompt in ["/image a robot", "Generate an image of a dog", "Please draw a robot",
                       "Shady, can you make a picture of a lab?", "Paint a portrait of my dad who died"]:
            self.assertEqual(router.route(prompt), "image", prompt)
        for prompt in ["How does image generation work?", "Write Python code to generate an image",
                       "Find a photo of Decatur", "Can you generate images?", "Draw attention to the bug"]:
            self.assertNotEqual(router.route(prompt), "image", prompt)

    async def test_disabled_feature_never_calls_provider(self):
        with patch.dict(os.environ, {"IMAGE_GENERATION_ENABLED": "false"}), self.client(lambda request:
                self.fail("Disabled images must not call the provider")):
            with self.assertRaises(ImageGenerationError):
                await generate_image("/image a robot")

    async def test_success_sends_server_key_and_returns_jpeg(self):
        def handler(request):
            self.assertEqual(request.headers["authorization"], "Bearer private-test-key")
            body = json.loads(request.content)
            self.assertEqual(body["prompt"], "a robot")
            self.assertEqual(body["n"], 1)
            self.assertEqual(body["output_format"], "jpeg")
            return httpx.Response(200, json={"data": [{"b64_json": JPEG}]})
        with self.client(handler):
            result = await generate_image("/image a robot")
        self.assertEqual(result["data"], JPEG)
        self.assertEqual(result["mime_type"], "image/jpeg")

    async def test_invalid_payload_and_upstream_secrets_are_sanitized(self):
        for status, payload in [(200, {"data": []}), (200, {"data": [{"b64_json": "abcd"}]}),
                                (500, {"error": "private-test-key"}), (401, {"error": "private-test-key"})]:
            with self.client(lambda request: httpx.Response(status, json=payload)):
                with self.assertRaises(ImageGenerationError) as raised:
                    await generate_image("/image a robot")
            self.assertNotIn("private-test-key", str(raised.exception))

    async def test_empty_and_oversized_descriptions_are_rejected(self):
        for prompt in ["/image", "/image " + "a" * 4001]:
            with self.assertRaises(ImageGenerationError) as raised:
                await generate_image(prompt)
            self.assertEqual(raised.exception.status_code, 400)

    async def test_streamed_image_bypasses_search_and_text_provider(self):
        request = main.ChatRequest(message="/image A robot", stream=True, session_id="image-test")
        with patch("main.generate_image", new=AsyncMock(return_value=IMAGE)), \
             patch("main.prepare_chat", new=AsyncMock(side_effect=AssertionError("Text route used"))):
            events = [json.loads(record) async for record in main.chat_events(request, "image")]
        self.assertEqual(events[0]["stage"], "generating_image")
        self.assertEqual(next(item for item in events if item["type"] == "image")["image"], IMAGE)
        self.assertEqual(events[-1]["type"], "done")
        self.assertNotIn(JPEG, json.dumps(main.memory.get_history("image-test")))

    async def test_json_image_response(self):
        with patch("main.generate_image", new=AsyncMock(return_value=IMAGE)):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app), base_url="http://test") as client:
                response = await client.post("/chat", json={"message": "/image A robot", "session_id": "image-json-test"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["image"], IMAGE)
        self.assertEqual(response.json()["capability"], "image")

    async def test_stream_failure_does_not_claim_image_success(self):
        request = main.ChatRequest(message="/image A robot", session_id="image-failed-test")
        with patch("main.generate_image", new=AsyncMock(side_effect=ImageGenerationError("Provider unavailable"))):
            events = [json.loads(record) async for record in main.chat_events(request, "image")]
        self.assertEqual(events[-1]["type"], "error")
        self.assertFalse(any(item["type"] in ["image", "done"] for item in events))
        self.assertEqual(main.memory.get_history("image-failed-test"), [])

    async def test_cancelled_provider_request_releases_image_slot(self):
        started = asyncio.Event()

        async def waiting(request):
            started.set()
            await asyncio.Event().wait()

        with self.client(waiting):
            task = asyncio.create_task(generate_image("/image a robot"))
            await started.wait()
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        with self.client(lambda request: httpx.Response(200, json={"data": [{"b64_json": JPEG}]})):
            result = await generate_image("/image another robot")
        self.assertEqual(result["data"], JPEG)


if __name__ == "__main__":
    unittest.main()
