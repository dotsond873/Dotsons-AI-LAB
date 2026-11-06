"""Text-to-image requests through the OpenAI Images API."""
import asyncio
import base64
import binascii
import os
import re

import httpx

_slots = asyncio.Semaphore(1)
_prefix = r"^(?:shady[,!]?\s+)?(?:please\s+)?(?:(?:can|could|would)\s+you\s+)?"
_creation = re.compile(
    _prefix + r"(?:create|generate|make|design|render)\s+(?:me\s+)?"
    r"(?:an?\s+)?(?:[\w-]+\s+){0,3}"
    r"(?:image|picture|photo|photograph|illustration|logo|poster|artwork|painting|drawing|scene)"
    r"\s*(?::|of\b|showing\b|featuring\b|for\b|with\b|depicting\b)\s*\S", re.I,
)
_drawing = re.compile(_prefix + r"(?:draw|paint|illustrate)\s+(?:me\s+)?(?:an?\s+|the\s+)\S", re.I)


class ImageGenerationError(Exception):
    def __init__(self, message, status_code=503):
        super().__init__(message)
        self.status_code = status_code


def is_image_request(message):
    return message.split(maxsplit=1)[:1] == ["/image"] or bool(
        _creation.search(message.strip()) or _drawing.search(message.strip())
    )


def image_configuration():
    return {
        "enabled": os.getenv("IMAGE_GENERATION_ENABLED", "").lower() == "true",
        "configured": bool(os.getenv("OPENAI_API_KEY", "").strip()),
        "model": os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2.5-sunburst"),
    }


async def generate_image(message):
    prompt = message.strip()
    if prompt.split(maxsplit=1)[:1] == ["/image"]:
        prompt = prompt[len("/image"):].strip()
    if not prompt:
        raise ImageGenerationError("Describe the image after /image. For example, /image a robot working in Dotson Labs.", 400)
    if len(prompt) > 4000:
        raise ImageGenerationError("Please keep the image description under 4,000 characters.", 400)
    config = image_configuration()
    if not config["enabled"] or not config["configured"]:
        raise ImageGenerationError("Image creation needs to be activated by the app owner. The image provider is not connected yet.")
    try:
        await asyncio.wait_for(_slots.acquire(), timeout=0.1)
    except TimeoutError:
        raise ImageGenerationError("Shady is creating another image. Try again when it finishes.", 429) from None
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(150, connect=10)) as client:
            response = await client.post(
                "https://api.openai.com/v1/images/generations",
                headers={"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"]},
                json={"model": config["model"], "prompt": prompt, "n": 1,
                      "size": "1024x1024", "quality": "medium",
                      "output_format": "jpeg", "output_compression": 80},
            )
        if response.status_code in (401, 403):
            raise ImageGenerationError("The image provider needs the owner's attention. Check the API key and image-model access.")
        if response.status_code == 429:
            raise ImageGenerationError("The image provider's quota or rate limit was reached. Please try again later.", 429)
        if response.status_code == 400:
            raise ImageGenerationError("The image provider could not accept this request. Try a different image description.", 400)
        response.raise_for_status()
        data = response.json()["data"][0]["b64_json"]
        if not isinstance(data, str) or len(data) > 12_000_000:
            raise ValueError("Invalid image response size")
        decoded = base64.b64decode(data, validate=True)
        if not decoded.startswith(b"\xff\xd8\xff"):
            raise ValueError("Expected a JPEG image")
        return {"data": data, "mime_type": "image/jpeg", "prompt": prompt, "model": config["model"]}
    except ImageGenerationError:
        raise
    except httpx.TimeoutException:
        raise ImageGenerationError("The image provider took too long. Please try again.", 504) from None
    except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError, binascii.Error):
        raise ImageGenerationError("Shady couldn't finish creating the image. Please try again.", 502) from None
    finally:
        _slots.release()
