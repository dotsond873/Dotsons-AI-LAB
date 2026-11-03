import test from "node:test";
import assert from "node:assert/strict";
import { newConversation, freshState, appendMessage, saveConversations, loadConversations, deleteConversation, requestHistory } from "./conversations.mjs";
const memoryStorage = () => { const values = new Map(); return { getItem:k=>values.get(k)||null, setItem:(k,v)=>values.set(k,v) }; };

test("new chats have unique ids and do not share messages", () => {
  let state = freshState(); const first = state.activeId; const second = newConversation();
  state = { ...state, chats:[...state.chats, second] };
  state = appendMessage(state, first, {role:"user",text:"My name is David"});
  assert.notEqual(first, second.id);
  assert.equal(state.chats[1].messages.length, 1);
  assert.equal(state.chats[0].title, "My name is David");
});
test("save and reload restore active chat, sources, and history without page bodies", () => {
  const storage = memoryStorage(); let state = freshState();
  state = appendMessage(state, state.activeId, {role:"user",text:"Hello"});
  state = appendMessage(state, state.activeId, {role:"assistant",text:"Hi", sources:[{url:"https://example.com", title:"Source", page_text:"huge excerpt", date:"Nov 3, 2026"}]});
  assert.equal(saveConversations(storage,state),"");
  const restored = loadConversations(storage);
  assert.equal(restored.activeId,state.activeId);
  assert.equal(restored.chats[0].messages[2].sources[0].page_text,undefined);
  assert.equal(requestHistory(restored.chats[0].messages).length,2);
});
test("errors and greeting are excluded from model history", () => {
  const messages=[{role:"assistant",text:"Welcome",greeting:true},{role:"user",text:"Hi"},{role:"assistant",text:"Failed",error:true}];
  assert.deepEqual(requestHistory(messages),[{role:"user",content:"Hi"}]);
});
test("delete last chat creates an independent empty chat", () => {
  const state=freshState(); const after=deleteConversation(state,state.activeId);
  assert.notEqual(after.activeId,state.activeId);
  assert.equal(after.chats.length,1);
  assert.deepEqual(requestHistory(after.chats[0].messages),[]);
});
test("corrupt storage and unavailable storage do not crash", () => {
  assert.ok(loadConversations({getItem:()=>"{broken"}).notice);
  assert.ok(saveConversations({setItem:()=>{throw new Error("quota");}},freshState()));
});
test("history is capped and unsafe source URLs are not saved", () => {
  const history=requestHistory(Array.from({length:30},(_,i)=>({role:"user",text:String(i)})));
  assert.equal(history.length,20); assert.equal(history[0].content,"10");
  let state=freshState();state=appendMessage(state,state.activeId,{role:"assistant",text:"link",sources:[{url:"javascript:alert(1)"}]});
  assert.equal(state.chats[0].messages[1].sources.length,0);
});

