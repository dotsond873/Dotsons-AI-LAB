import test from "node:test";
import assert from "node:assert/strict";
import { freshState, newConversation, setPersonality, saveConversations, loadConversations } from "./conversations.mjs";
test("style is independent for each chat",()=>{
  let state=freshState();const first=state.activeId,second=newConversation();
  state={...state,chats:[...state.chats,second]};
  state=setPersonality(state,first,"professional");
  assert.equal(state.chats[0].personality,"professional");
  assert.equal(state.chats[1].personality,"shady");
  assert.equal(setPersonality(state,first,"invalid"),state);
});
test("style survives reload and older chats default to Shady",()=>{
  let state=freshState();state=setPersonality(state,state.activeId,"direct");
  let raw;const storage={getItem:()=>raw,setItem:(_,value)=>raw=value};
  saveConversations(storage,state);
  assert.equal(loadConversations(storage).chats[0].personality,"direct");
  const old=JSON.parse(raw);delete old.chats[0].personality;raw=JSON.stringify(old);
  assert.equal(loadConversations(storage).chats[0].personality,"shady");
});

