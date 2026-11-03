import test from "node:test";
import assert from "node:assert/strict";
import { readAnswerStream } from "./answer-stream.mjs";
import { freshState, appendMessage, updateMessage, requestHistory, saveConversations, loadConversations } from "./conversations.mjs";
function response(text, size=1) {
  const bytes=new TextEncoder().encode(text);
  return {body:new ReadableStream({start(controller){for(let i=0;i<bytes.length;i+=size)controller.enqueue(bytes.slice(i,i+size));controller.close();}})};
}
test("handles split UTF-8, multiple records, and final record without newline", async()=>{
  const seen=[];
  await readAnswerStream(response('{"type":"meta"}\n{"type":"delta","text":"Hello 😀"}\n{"type":"done"}'),e=>seen.push(e));
  assert.equal(seen[1].text,"Hello 😀");assert.equal(seen[2].type,"done");
});
test("disconnection and server error are surfaced",async()=>{
  await assert.rejects(()=>readAnswerStream(response('{"type":"delta","text":"Partial"}\n'),()=>{}),/before Shady finished/);
  await assert.rejects(()=>readAnswerStream(response('{"type":"error","message":"Try again"}\n'),()=>{}),/Try again/);
});
test("updates one assistant message and excludes interrupted saved replies",()=>{
  let state=freshState(), id=state.activeId;
  state=appendMessage(state,id,{id:"reply",role:"assistant",text:"",incomplete:true});
  state=updateMessage(state,id,"reply",{text:"Hello"});
  assert.equal(state.chats[0].messages.length,2);
  assert.deepEqual(requestHistory(state.chats[0].messages),[]);
  let saved; const storage={setItem:(_,v)=>saved=v,getItem:()=>saved};
  saveConversations(storage,state);
  const restored=loadConversations(storage);
  assert.equal(restored.chats[0].messages[1].error,true);
  assert.match(restored.chats[0].messages[1].text,/interrupted/);
  state=updateMessage(state,id,"reply",{text:"Hello world",incomplete:false});
  assert.equal(requestHistory(state.chats[0].messages)[0].content,"Hello world");
});

