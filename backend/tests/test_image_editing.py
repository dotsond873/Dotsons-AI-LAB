import base64
import json
import os
import unittest
from unittest.mock import AsyncMock, patch
import httpx
from core.attachments import Attachment
from core.image_generation import generate_image, is_image_edit_request, ImageGenerationError
os.environ.setdefault('GROQ_API_KEY', 'test-key')
import main
JPEG = base64.b64encode(b'\xff\xd8\xfftest-source').decode()
PHOTO = Attachment(name='selfie.jpg', data=JPEG)
RESULT = {'data':JPEG, 'mime_type':'image/jpeg', 'prompt':'age me to 80', 'model':'test-model'}

class ImageEditingTests(unittest.IsolatedAsyncioTestCase):
    def test_edit_intent_and_read_intent(self):
        for message in ['age enhance this photo to me at age 80', 'Please age me to 80', '/edit age me to 80', 'Remove the background', 'Can you retouch this photo?', 'Make me look 80 years old']:
            self.assertTrue(is_image_edit_request(message), message)
        for message in ['Describe this photo', 'How can I edit this image?', 'Tell me the age of this person', 'What does age enhancement mean?']:
            self.assertFalse(is_image_edit_request(message), message)

    async def test_edit_posts_actual_source_pixels(self):
        def handler(request):
            self.assertEqual(request.url.path, '/v1/images/edits')
            body = json.loads(request.content)
            self.assertEqual(body['images'][0]['image_url'], 'data:image/jpeg;base64,' + JPEG)
            self.assertIn('age me to 80', body['prompt'])
            self.assertEqual(body['output_format'], 'jpeg')
            return httpx.Response(200, json={'data':[{'b64_json':JPEG}]})
        constructor = httpx.AsyncClient
        with patch.dict(os.environ, {'IMAGE_GENERATION_ENABLED':'true', 'OPENAI_API_KEY':'private-test-key'}), patch('core.image_generation.httpx.AsyncClient', side_effect=lambda **kw: constructor(transport=httpx.MockTransport(handler), **kw)):
            result = await generate_image('/edit age me to 80', [PHOTO])
        self.assertEqual(result['data'], JPEG)

    async def test_missing_photo_and_documents_rejected(self):
        for attachments in [[], [Attachment(name='text.txt', data=base64.b64encode(b'hello').decode())]]:
            with self.assertRaises(ImageGenerationError) as error:
                await generate_image('/edit age me to 80', attachments)
            self.assertEqual(error.exception.status_code, 400)

    async def test_routes_json_and_stream_to_edit_not_reader(self):
        payload = {'message':'age enhance this photo to me at age 80', 'attachments':[PHOTO.model_dump()]}
        with patch('main.generate_image', new=AsyncMock(return_value=RESULT)) as generate, patch('main.prepare_chat', new=AsyncMock(side_effect=AssertionError('Reader used'))):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app), base_url='http://test') as client:
                result = await client.post('/chat', json=payload)
                self.assertEqual(result.json()['capability'], 'image_edit')
                self.assertEqual(generate.call_args.args[1][0].data, JPEG)
                result = await client.post('/chat', json={**payload, 'stream':True})
                events = [json.loads(line) for line in result.text.splitlines()]
                self.assertEqual(events[0]['stage'], 'editing_image')
                self.assertEqual(events[-1]['type'], 'done')
                self.assertTrue(any(e['type'] == 'image' for e in events))

    async def test_disabled_edit_reports_setting_instead_of_chat_refusal(self):
        with patch.dict(os.environ, {'IMAGE_GENERATION_ENABLED':'false', 'OPENAI_API_KEY':'test-key'}):
            events = [json.loads(line) async for line in main.chat_events(main.ChatRequest(message='age me to 80', attachments=[PHOTO]), 'image_edit')]
        self.assertEqual(events[-1]['type'], 'error')
        self.assertIn('IMAGE_GENERATION_ENABLED', events[-1]['message'])
        self.assertFalse(any(e['type'] in ('done', 'image') for e in events))
