import os
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('GROQ_API_KEY', 'local-test-placeholder')
import main
from core.search_policy import should_search


class HistoricalSearchTests(unittest.TestCase):
    def test_historical_results_use_knowledge(self):
        for question in ('who won the 1976 superbowl', 'Who won the 1976 Super Bowl?',
                         'What was the score of the 1976 Super Bowl?',
                         'Who won the 1998 World Cup?', 'Who won the 2004 World Series?'):
            with self.subTest(question=question):
                self.assertFalse(should_search(question))

    def test_explicit_verification_still_searches(self):
        for question in ('Search who won the 1976 superbowl',
                         'Verify who won the 1976 Super Bowl',
                         'Who won the 1976 Super Bowl? Give sources.'):
            self.assertTrue(should_search(question))
        self.assertTrue(should_search('who won the 1976 superbowl', True))
        self.assertFalse(should_search('who won the Super Bowl today', False))

    def test_fresh_and_mixed_requests_still_search(self):
        for question in ('Who won the Super Bowl?', 'Who won the Super Bowl today?',
                         'Latest news about the 1976 Super Bowl winner',
                         'Who won the 1976 and 2099 Super Bowls?',
                         'Birmingham news today'):
            self.assertTrue(should_search(question))


class HistoricalChatTests(unittest.IsolatedAsyncioTestCase):
    async def test_auto_history_question_survives_unavailable_search(self):
        with patch.object(main, 'search_web', AsyncMock(side_effect=RuntimeError('search unavailable'))) as search:
            prompt, sources, status = await main.prepare_chat(main.ChatRequest(
                message='who won the 1976 superbowl', history=[]), 'chat')
        search.assert_not_awaited()
        self.assertEqual(sources, [])
        self.assertEqual(status, 'not_requested')
        self.assertIn('who won the 1976 superbowl', prompt)


if __name__ == '__main__':
    unittest.main()
