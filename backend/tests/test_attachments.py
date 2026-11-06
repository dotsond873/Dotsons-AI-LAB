import base64
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock
from fastapi import HTTPException
from core.attachments import Attachment, decode_attachment, attachment_context


def item(name, data):
    return Attachment(name=name, data=base64.b64encode(data).decode())

class AttachmentTests(unittest.IsolatedAsyncioTestCase):
    def test_text_and_type_validation(self):
        self.assertEqual(decode_attachment(item('code.py', b'print(42)')), ('text', 'print(42)'))
        for file in [item('bad.exe', b'hello'), item('fake.png', b'hello'), item('null.txt', b'\0'), item('big.txt', b'x' * (2*1024*1024+1))]:
            with self.assertRaises((HTTPException, ValueError)):
                decode_attachment(file)

    def test_bad_base64(self):
        with self.assertRaises(HTTPException):
            decode_attachment(Attachment(name='file.txt', data='???'))

    async def test_photo_reaches_vision_api(self):
        create = AsyncMock(return_value=SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='A red car'))]))
        provider = SimpleNamespace(client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
        text = await attachment_context([item('photo.jpg', b'\xff\xd8\xfftest')], provider, 'What color?')
        self.assertIn('A red car', text)
        args = create.call_args.kwargs
        self.assertTrue(args['messages'][0]['content'][1]['image_url']['url'].startswith('data:image/jpeg;base64,'))

    async def test_provider_error_is_actionable(self):
        create = AsyncMock(side_effect=RuntimeError('secret error'))
        provider = SimpleNamespace(client=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create))))
        with self.assertRaises(HTTPException) as error:
            await attachment_context([item('photo.jpg', b'\xff\xd8\xfftest')], provider, 'Describe')
        self.assertNotIn('secret', str(error.exception.detail))

    async def test_text_context_bounded_and_marked(self):
        text = await attachment_context([item('file.txt', b'x'*20000)], None, '')
        self.assertIn('untrusted reference data', text)
        self.assertIn('truncated', text)
        self.assertLess(len(text), 16500)

    async def test_json_and_stream_include_file_contents(self):
        import os, json, httpx
        from unittest.mock import patch
        os.environ.setdefault('GROQ_API_KEY', 'test-key')
        import main
        async def stream(prompt):
            self.assertIn('invoice total 42', prompt)
            yield 'The total is 42.'
        fake = SimpleNamespace(model='test', generate=AsyncMock(return_value='The total is 42.'), stream=stream)
        payload = {'message':'Review this', 'web_search':True, 'history':[], 'attachments':[item('invoice.txt', b'invoice total 42').model_dump()]}
        with patch('main.provider', fake), patch('main.search_web', side_effect=AssertionError('Unexpected search')):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app), base_url='http://test') as client:
                response = await client.post('/chat', json=payload)
                self.assertEqual(response.status_code, 200)
                self.assertIn('invoice total 42', fake.generate.call_args.args[0])
                response = await client.post('/chat', json={**payload, 'stream':True})
                events = [json.loads(line) for line in response.text.splitlines()]
                self.assertEqual(events[-1]['type'], 'done')
                response = await client.post('/chat', json={**payload, 'attachments':[item('bad.exe', b'bad').model_dump()]})
                self.assertEqual(response.status_code, 400)
