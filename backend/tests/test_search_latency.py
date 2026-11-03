import asyncio
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('GROQ_API_KEY', 'local-test-placeholder')
import httpx
import main
from core import web_search
from core.web_search import SearchUnavailable


class SearchLatencyTests(unittest.IsolatedAsyncioTestCase):
    async def test_status_arrives_before_search_starts(self):
        request = main.ChatRequest(message='Birmingham news today', stream=True)
        with patch.object(main, 'search_web', AsyncMock(return_value=[])) as search:
            events = main.chat_events(request, 'chat')
            self.assertEqual(json.loads(await anext(events)), {'type':'status', 'stage':'searching'})
            search.assert_not_awaited()
            self.assertEqual(json.loads(await anext(events))['stage'], 'thinking')
            search.assert_awaited_once()
            await events.aclose()

    async def test_no_search_for_search_off(self):
        request = main.ChatRequest(message='Birmingham news today', stream=True, web_search=False)
        with patch.object(main, 'search_web', AsyncMock()) as search:
            events = main.chat_events(request, 'chat')
            self.assertEqual(json.loads(await anext(events))['stage'], 'thinking')
            self.assertEqual(json.loads(await anext(events))['type'], 'meta')
            search.assert_not_awaited()
            await events.aclose()

    async def test_search_failure_is_streamed_without_memory_save(self):
        request = main.ChatRequest(message='news', stream=True, session_id='latency-error-test')
        with patch.object(main, 'search_web', AsyncMock(side_effect=SearchUnavailable('Web search timed out. Please try again.', 504))):
            records = [json.loads(line) async for line in main.chat_events(request, 'chat')]
        self.assertEqual(records[-1]['type'], 'error')
        self.assertEqual(records[-1]['status_code'], 504)
        self.assertEqual(main.memory.get_history(request.session_id), [])

    async def test_total_search_deadline_cancels_work(self):
        closed = []
        async def slow(query):
            try:
                await asyncio.sleep(10)
            finally:
                closed.append(True)
        with patch.object(web_search, '_search_web', slow), patch.object(web_search, 'SEARCH_BUDGET_SECONDS', 0.01):
            with self.assertRaises(SearchUnavailable) as error:
                await web_search.search_web('news')
        self.assertEqual(error.exception.status_code, 504)
        self.assertEqual(closed, [True])

    async def test_page_extraction_is_selective(self):
        original_client = httpx.AsyncClient
        for query, expected_reads in [('search for widgets', 0), ('read the article https://example.com/story', 1)]:
            urls = []
            def respond(request):
                urls.append(request.url.path)
                if request.url.path.endswith('.md'):
                    return httpx.Response(200, text='An extracted page excerpt', headers={'content-type':'text/markdown'})
                return httpx.Response(200, json={'organic_results':[
                    {'link':'https://example.com/story','title':'Widget story'},
                    {'link':'https://example.com/other','title':'Other story'}]})
            def client(**kwargs):
                return original_client(**kwargs, transport=httpx.MockTransport(respond), trust_env=False)
            with patch.dict(os.environ, {'SERPAPI_API_KEY':'test-placeholder'}), patch.object(web_search.httpx, 'AsyncClient', client):
                sources = await web_search.search_web(query)
            self.assertEqual(urls.count('/search.md'), expected_reads)
            self.assertEqual(sources[0]['page_status'], 'read' if expected_reads else 'not_read')


if __name__ == '__main__':
    unittest.main()
