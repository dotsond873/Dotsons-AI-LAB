import asyncio, json, unittest
from types import SimpleNamespace
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.streaming import answer_events

class Memory:
    def __init__(self): self.items=[]
    def add_message(self,*args): self.items.append(args)

class StreamTests(unittest.IsolatedAsyncioTestCase):
    async def test_deltas_arrive_before_memory_is_saved(self):
        class Provider:
            model="fake"
            async def stream(self,prompt):
                yield "Hello "
                yield "world"
        memory=Memory()
        gen=answer_events(Provider(),"prompt",SimpleNamespace(session_id="a",message="hi"),"chat",[{"url":"https://example.com","page_text":"private context"}],"completed",memory)
        meta=json.loads(await anext(gen))
        self.assertNotIn("page_text",meta["sources"][0])
        self.assertEqual(json.loads(await anext(gen)),{"type":"delta","text":"Hello "})
        self.assertEqual(memory.items,[])
        self.assertEqual(json.loads(await anext(gen))["text"],"world")
        self.assertEqual(json.loads(await anext(gen))["type"],"done")
        self.assertEqual(memory.items[-1],("a","assistant","Hello world"))
        await gen.aclose()
    async def test_failure_is_sanitized_and_not_saved(self):
        class Provider:
            model="fake"
            async def stream(self,prompt):
                yield "Partial"
                raise RuntimeError("secret-key")
        memory=Memory()
        records=[json.loads(record) async for record in answer_events(Provider(),"p",SimpleNamespace(session_id="a",message="hi"),"chat",[],"not_requested",memory)]
        self.assertEqual(records[-1]["type"],"error")
        self.assertNotIn("secret-key",str(records))
        self.assertEqual(memory.items,[])
    async def test_disconnect_closes_provider_and_does_not_save_partial(self):
        closed=[]
        class Provider:
            model="fake"
            async def stream(self,prompt):
                try:
                    yield "Partial"
                    yield "rest"
                finally: closed.append(True)
        memory=Memory()
        gen=answer_events(Provider(),"p",SimpleNamespace(session_id="a",message="hi"),"chat",[],"not_requested",memory)
        await anext(gen); await anext(gen); await gen.aclose()
        self.assertEqual(closed,[True])
        self.assertEqual(memory.items,[])
if __name__=="__main__": unittest.main()

