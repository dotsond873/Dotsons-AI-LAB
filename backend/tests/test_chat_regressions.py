import os
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('GROQ_API_KEY', 'local-test-placeholder')
from fastapi.testclient import TestClient
import main
from core.local_news import local_news_city, relevant_local_result, news_search_params
from core.prompt_budget import MAX_PROMPT_BYTES, fit_history


class CityNewsTests(unittest.TestCase):
    def test_supported_city_wording(self):
        for city in ('Decatur', 'Birmingham'):
            for query in (f'Give me the latest {city} AL news', f'{city} news today',
                          f'What is the latest local news in {city}, Alabama?',
                          f'Today’s {city} headlines'):
                with self.subTest(query=query):
                    self.assertEqual(local_news_city(query), city.lower())
                    self.assertEqual(news_search_params(query)['tbm'], 'nws')

    def test_explicit_other_places_and_world_news(self):
        for query in ('Decatur Georgia news', 'Birmingham England news',
                      'World news from Decatur Alabama', 'Explain Birmingham architecture'):
            self.assertIsNone(local_news_city(query))

    def test_bare_city_uses_same_outlet_rules(self):
        self.assertFalse(relevant_local_result({'link':'https://example.com/story',
                         'title':'Decatur news'}, 'Decatur news today'))
        self.assertTrue(relevant_local_result({'link':'https://decaturdaily.com/news/story',
                        'title':'Morgan County project'}, 'Decatur news today'))


class PromptTests(unittest.TestCase):
    def test_retains_earlier_context_beyond_old_600_byte_tail(self):
        history = [{'role':'user','content':'My test code is MAPLE-42.'},
                   {'role':'assistant','content':'Workshop advice. ' * 70}]
        prompt = main.build_prompt('What is my code?', 'test', 'chat', history=history)
        self.assertIn('MAPLE-42', prompt)
        self.assertLessEqual(len(prompt.encode('utf-8')), MAX_PROMPT_BYTES)

    def test_budget_with_search_and_unicode(self):
        for message in ('Short question', '😀' * 400):
            prompt = main.build_prompt(message, 'test', 'chat',
                       search_context='fresh evidence ' * 1000,
                       history=[{'role':'user','content':'😀' * 2000}])
            self.assertLessEqual(len(prompt.encode('utf-8')), MAX_PROMPT_BYTES)
        self.assertEqual(fit_history([{'role':'user','content':'hello'}], 0), '')

    def test_recent_messages_remain_in_order(self):
        history = [{'role':'user','content':'old' * 1000},
                   {'role':'user','content':'recent question'},
                   {'role':'assistant','content':'recent answer'}]
        self.assertEqual(fit_history(history, 100),
                         '\nUSER: recent question\nASSISTANT: recent answer')


class ErrorTests(unittest.TestCase):
    def test_nonstream_provider_failure_is_sanitized(self):
        with patch.object(main.provider, 'generate', AsyncMock(side_effect=RuntimeError(
                'secret-key https://provider.invalid/?api_key=secret-key'))):
            response = TestClient(main.app).post('/chat', json={
                'message':'hello', 'session_id':'test-failure', 'web_search':False})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()['detail'], "Shady couldn't complete this request. Please try again.")
        self.assertNotIn('secret-key', response.text)
        self.assertEqual(main.memory.get_history('test-failure'), [])

    def test_failure_before_stream_headers_is_sanitized(self):
        with patch.object(main, 'build_prompt', side_effect=RuntimeError('secret-key')):
            response = TestClient(main.app).post('/chat', json={
                'message':'hello', 'stream':True, 'web_search':False})
        self.assertEqual(response.status_code, 200)
        self.assertIn('"type": "error"', response.text)
        self.assertNotIn('secret-key', response.text)


if __name__ == '__main__':
    unittest.main()
