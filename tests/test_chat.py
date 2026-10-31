import sys
from pathlib import Path
from unittest.mock import AsyncMock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from fastapi.testclient import TestClient
import main

client = TestClient(main.app)

def test_missing_key_does_not_prevent_startup(monkeypatch):
    monkeypatch.setattr(main.provider, 'client', None)
    assert client.get('/health').json()['provider_ready'] is False
    assert client.post('/chat', json={'message': 'hello'}).status_code == 503

def test_conversations_are_isolated(monkeypatch):
    monkeypatch.setattr(main.provider, 'client', object())
    monkeypatch.setattr(main.provider, 'generate', AsyncMock(return_value='Hello David'))
    first = client.post('/chat', json={'message': 'first secret'})
    second = client.post('/chat', json={'message': 'second secret'})
    assert first.status_code == second.status_code == 200
    a, b = first.json()['session_id'], second.json()['session_id']
    assert a != b
    history = client.get(f'/memory/{a}').json()['history']
    assert history[0]['content'] == 'first secret'
    assert client.delete(f'/memory/{a}').json()['cleared'] is True
    assert client.get(f'/memory/{a}').json()['history'] == []
    assert client.get(f'/memory/{b}').json()['history']

def test_empty_messages_rejected(monkeypatch):
    assert client.post('/chat', json={'message': '  '}).status_code == 422
    assert client.post('/chat', json={'message': 'hello', 'session_id': 'default'}).status_code == 422
