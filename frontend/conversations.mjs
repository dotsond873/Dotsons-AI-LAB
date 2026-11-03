export const STORAGE_KEY = "odb-conversations-v1";
export const GREETING = "ODB SHADY 6.9 online. What kind of trouble are we getting into?";

export function newConversation() {
  return { id: crypto.randomUUID(), title: "New chat", updatedAt: new Date().toISOString(),
    messages: [{ role: "assistant", text: GREETING, greeting: true }] };
}

export function freshState(notice = "") {
  const chat = newConversation();
  return { version: 1, chats: [chat], activeId: chat.id, notice };
}

function safeMessage(message) {
  if (!message || !["user", "assistant"].includes(message.role) || typeof message.text !== "string") return null;
  const result = { role: message.role, text: message.text };
  for (const key of ["id", "incomplete", "greeting", "error", "capability", "searchStatus"]) {
    if (message[key] !== undefined) result[key] = message[key];
  }
  if (message.incomplete) result.incomplete = true;
  if (Array.isArray(message.sources)) {
    result.sources = message.sources.filter(s => s && typeof s.url === "string" && (s.url.startsWith("https://") || s.url.startsWith("http://")))
      .map(s => ({ title: s.title || s.url, url: s.url, date: s.date || "", page_status: s.page_status || "not_read" }));
  }
  return result;
}

export function loadConversations(storage) {
  try {
    const raw = storage.getItem(STORAGE_KEY);
    if (!raw) return freshState();
    const saved = JSON.parse(raw);
    if (saved.version !== 1 || !Array.isArray(saved.chats)) throw new Error("Invalid saved chats");
    const ids = new Set();
    const chats = saved.chats.filter(c => c && typeof c.id === "string" && /^[a-zA-Z0-9-]{10,100}$/.test(c.id) && Array.isArray(c.messages))
      .filter(c => { if (ids.has(c.id)) return false; ids.add(c.id); return true; })
      .map(c => ({ id: c.id, title: typeof c.title === "string" ? c.title.slice(0, 80) : "Saved chat",
        updatedAt: c.updatedAt || "", messages: c.messages.map(safeMessage).filter(Boolean).map(m => m.incomplete ? { ...m, incomplete:false, error:true, text:(m.text || "") + "\n\nResponse interrupted before completion." } : m) }));
    if (!chats.length) return freshState();
    return { version: 1, chats, activeId: chats.some(c => c.id === saved.activeId) ? saved.activeId : chats[0].id, notice: "" };
  } catch {
    return freshState("Saved chats could not be loaded. This conversation is available in this tab.");
  }
}

export function saveConversations(storage, state) {
  try {
    storage.setItem(STORAGE_KEY, JSON.stringify({ version: 1, activeId: state.activeId,
      chats: state.chats.map(c => ({ ...c, messages: c.messages.map(safeMessage).filter(Boolean) })) }));
    return "";
  } catch {
    return "Chats cannot be saved right now. Keep this tab open; browser storage may be full or unavailable.";
  }
}

export function appendMessage(state, id, message) {
  return { ...state, chats: state.chats.map(c => c.id !== id ? c : {
    ...c, title: message.role === "user" && !c.messages.some(m => m.role === "user") && c.title === "New chat"
      ? message.text.slice(0, 48) : c.title,
    updatedAt: new Date().toISOString(), messages: [...c.messages, safeMessage(message)]
  }) };
}

export function deleteConversation(state, id) {
  const chats = state.chats.filter(c => c.id !== id);
  if (!chats.length) return freshState();
  return { ...state, chats, activeId: state.activeId === id ? chats[0].id : state.activeId };
}

export function requestHistory(messages) {
  return messages.filter(m => !m.greeting && !m.error && !m.incomplete).slice(-20)
    .map(m => ({ role: m.role, content: m.text.slice(0, 20000) }));
}

export function updateMessage(state, chatId, messageId, patch) {
  return { ...state, chats: state.chats.map(chat => chat.id !== chatId ? chat : {
    ...chat, messages: chat.messages.map(message => message.id === messageId
      ? safeMessage({ ...message, ...patch }) : message)
  }) };
}
