
import { useState, useEffect, useRef } from "react";
import { loadConversations, saveConversations, newConversation, appendMessage, updateMessage, deleteConversation, requestHistory, setPersonality } from "./conversations.mjs";
import { readAnswerStream } from "./answer-stream.mjs";
import labArt from "./assets/odb-lab-v2.webp";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
const API_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

function ShareShady() {
  const [notice, setNotice] = useState("");
  const url = new URL("/", window.location.origin).href;

  async function share() {
    setNotice("");
    if (navigator.share) {
      try {
        await navigator.share({ title: "ODB SHADY 6.9", url });
        return;
      } catch (error) {
        if (error.name === "AbortError") return;
      }
    }
    try {
      await navigator.clipboard.writeText(url);
      setNotice("Link copied");
    } catch {
      setNotice("Copy this link");
    }
  }

  return (
    <div className="share-shady">
      <button type="button" className="share-button" onClick={share}>Share Shady</button>
      {notice && <div className="share-notice" role="status">
        {notice}
        {notice === "Copy this link" && (
          <input aria-label="Shady app link" readOnly value={url} onFocus={event => event.target.select()} />
        )}
      </div>}
    </div>
  );
}

export default function App() {
  const [entered, setEntered] = useState(false);
  const [conversations, setConversations] = useState(() => {
    try { return loadConversations(window.localStorage); }
    catch { return loadConversations({ getItem() { throw new Error("Storage unavailable"); } }); }
  });
  const [storageNotice, setStorageNotice] = useState(conversations.notice || "");
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [activity, setActivity] = useState("Shady is thinking…");
  const [webSearch, setWebSearch] = useState(null);
  const sending = useRef(false);
  const chatScroll = useRef(null);
  const inputBox = useRef(null);
  const followNewest = useRef(true);
  const [showJump, setShowJump] = useState(false);
  const activeChat = conversations.chats.find(c => c.id === conversations.activeId) || conversations.chats[0];
  const messages = activeChat.messages;

  useEffect(() => {
    try { setStorageNotice(saveConversations(window.localStorage, conversations)); }
    catch { setStorageNotice("Chats are only available in this tab because browser storage is unavailable."); }
  }, [conversations]);


  useEffect(() => {
    const box = inputBox.current;
    if (!box) return;
    box.style.height = "auto";
    box.style.height = Math.min(box.scrollHeight, 180) + "px";
  }, [input, entered]);

  useEffect(() => {
    followNewest.current = true;
    setShowJump(false);
    if (chatScroll.current) chatScroll.current.scrollTop = chatScroll.current.scrollHeight;
  }, [activeChat.id, entered]);

  useEffect(() => {
    if (followNewest.current && chatScroll.current) {
      chatScroll.current.scrollTop = chatScroll.current.scrollHeight;
    }
  }, [messages, loading, entered]);

  function trackScroll() {
    const box = chatScroll.current;
    if (!box) return;
    const nearBottom = box.scrollHeight - box.scrollTop - box.clientHeight < 100;
    followNewest.current = nearBottom;
    setShowJump(!nearBottom);
  }

  function jumpToLatest() {
    followNewest.current = true;
    setShowJump(false);
    if (chatScroll.current) chatScroll.current.scrollTop = chatScroll.current.scrollHeight;
  }

  function startChat() {
    if (sending.current) return;
    const chat = newConversation();
    setConversations(old => ({ ...old, chats: [chat, ...old.chats], activeId: chat.id }));
    setInput("");
  }

  function removeChat() {
    if (sending.current || !window.confirm("Delete this saved conversation from this browser?")) return;
    setConversations(old => deleteConversation(old, activeChat.id));
    setInput("");
  }

  function renameChat() {
    if (sending.current) return;
    const name = window.prompt("Conversation name", activeChat.title);
    if (!name?.trim()) return;
    setConversations(old => ({ ...old, chats: old.chats.map(c => c.id === activeChat.id ? { ...c, title: name.trim().slice(0, 80) } : c) }));
  }

  async function sendMessage() {
    const text = input.trim();
    if (!text || sending.current) return;
    sending.current = true;
    followNewest.current = true;
    setShowJump(false);
    const targetId = activeChat.id;
    const messageId = crypto.randomUUID();
    const history = requestHistory(activeChat.messages);
    let partial = "", started = false, flushTimer;
    function patch(patch) {
      setConversations(old => updateMessage(old, targetId, messageId, patch));
    }
    function flush(incomplete = true) {
      clearTimeout(flushTimer);
      flushTimer = undefined;
      patch({ text:partial, incomplete });
    }
    setConversations(old => appendMessage(old, targetId, { role:"user", text }));
    setInput("");
    setLoading(true);
    setStreaming(false);
    setActivity("Connecting to Shady…");
    try {
      const response = await fetch(`${API_URL}/chat`, {
        method:"POST", headers:{"Content-Type":"application/json"},
        body:JSON.stringify({ message:text, session_id:targetId, web_search:webSearch, history, stream:true, personality:activeChat.personality || "shady" }),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(typeof error.detail === "string" ? error.detail : "ODB backend returned an error.");
      }
      if ((response.headers.get("content-type") || "").includes("application/x-ndjson")) {
        await readAnswerStream(response, event => {
          if (event.type === "status") {
            setActivity(event.stage === "searching" ? "Searching the web…" : "Shady is thinking…");
          } else if (event.type === "meta") {
            started = true;
            setStreaming(true);
            setConversations(old => appendMessage(old, targetId, {
              id:messageId, role:"assistant", text:"", incomplete:true,
              capability:event.capability, sources:event.sources || [], searchStatus:event.search_status,
            }));
          } else if (event.type === "delta") {
            partial += event.text || "";
            if (!flushTimer) flushTimer = setTimeout(() => flush(), 75);
          } else if (event.type === "done") {
            flush(false);
          }
        });
      } else {
        // Compatible with the previous backend during a staggered deployment.
        const data = await response.json();
        setConversations(old => appendMessage(old, targetId, {
          role:"assistant", text:data.response, capability:data.capability,
          sources:data.sources || [], searchStatus:data.search_status,
        }));
      }
    } catch (error) {
      clearTimeout(flushTimer);
      const notice = (partial ? "\n\n" : "") + "Response interrupted: " + error.message;
      if (started) patch({ text:partial + notice, incomplete:false, error:true });
      else setConversations(old => appendMessage(old, targetId, { role:"assistant", text:notice, error:true }));
    } finally {
      clearTimeout(flushTimer);
      sending.current = false;
      setLoading(false);
      setStreaming(false);
    }
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing &&
        (!window.matchMedia("(pointer: coarse)").matches || event.ctrlKey || event.metaKey)) {
      event.preventDefault();
      sendMessage();
    }
  }

  if (!entered) return (
    <main className="lab-entrance">
      <style>{landingCss}</style>
      <img className="lab-art" src={labArt} alt="Humanoid AI working at illuminated consoles inside Dotson Labs" />
      <div className="lab-shade" />
      <nav className="lab-nav" aria-label="Main navigation">
        <a className="lab-brand" href="#home"><small>Dotson <b>Labs</b></small></a>
        <ShareShady />
      </nav>
      <section className="lab-copy" id="home">
        <p className="lab-eyebrow">WELCOME TO THE LAB</p>
        <h1>Intelligence.<br /><span>With attitude.</span></h1>
        <p className="lab-intro">Meet ODB SHADY 6.9. Your space to ask questions, explore ideas, and search the web.</p>
        <button className="lab-enter" onClick={() => { setEntered(true); window.scrollTo(0, 0); }}>Enter ODB SHADY 6.9 <span aria-hidden="true">↗</span></button>
        <p className="lab-hint">Step inside. Bring your curiosity.</p>
        <a className="lab-download" href="/download.html">Get Shady for your phone ↓</a>
      </section>
      <footer className="lab-footer"><span>DOTSON LABS / ARTIFICIAL INTELLIGENCE</span><span>ASK. EXPLORE. CREATE.</span></footer>
    </main>
  );

  return (
    <div className="chat-page">
      <style>{landingCss}</style>
      <header className="chat-header">
        <div>
          <div className="chat-logo">
            ODB SHADY 6.9
          </div>

          <button className="lab-back" onClick={() => setEntered(false)}>← DOTSON LABS</button>
        </div>

        <details className="chat-menu">
          <summary className="share-button">Menu</summary>
          <section className="conversation-tools" aria-label="Conversations">
            <div className="conversation-actions">
              <button onClick={startChat} disabled={loading}>+ New chat</button>
              <label>Saved chats{" "}
                <select aria-label="Saved conversations" value={activeChat.id} disabled={loading}
                  onChange={event => { setConversations(old => ({ ...old, activeId: event.target.value })); setInput(""); }}>
                  {conversations.chats.map(chat => <option key={chat.id} value={chat.id}>{chat.title}</option>)}
                </select>
              </label>
              <button onClick={renameChat} disabled={loading}>Rename</button>
              <button onClick={removeChat} disabled={loading}>Delete</button>
            </div>
            <p>{storageNotice || "Saved in this browser. Clearing browser data removes saved chats."}</p>

            <div className="chat-settings">
              <label className="search-control">
                Web search:{" "}
                <select aria-label="Web search mode" value={webSearch === null ? "auto" : webSearch ? "on" : "off"} disabled={loading}
                  onChange={(event) => setWebSearch(event.target.value === "auto" ? null : event.target.value === "on")}
                  >
                  <option value="auto">Auto — search when needed</option>
                  <option value="on">Always search</option>
                  <option value="off">Search off</option>
                </select>
              </label>
              <label className="search-control">
                Personality:{" "}
                <select aria-label="Shady personality" disabled={loading} value={activeChat.personality || "shady"}
                  onChange={event => setConversations(old => setPersonality(old, activeChat.id, event.target.value))}>
                  <option value="shady">Shady</option>
                  <option value="professional">Professional</option>
                  <option value="direct">Straight to the Point</option>
                </select>
              </label>
            </div>
            <ShareShady />
          </section>
        </details>
      </header>
      <main className="chat-feed" ref={chatScroll} onScroll={trackScroll} aria-label="Conversation messages" tabIndex={0}>
        {messages.map((message, index) => (
          <div
            key={index}
            className={`chat-message ${message.role === "user" ? "user-message" : "odb-message"}`}
          >
            <div className="message-role">
              {message.role === "user"
                ? "YOU"
                : "ODB"}
            </div>

            <div style={{ whiteSpace: "normal", overflowWrap: "anywhere" }}>
  {message.role === "assistant" ? (
    <div className="chat-markdown" style={{ overflowX: "auto" }}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {message.text || (message.incomplete ? "Shady is writing…" : "")}
      </ReactMarkdown>
    </div>
  ) : (
    <div style={{ whiteSpace: "pre-wrap" }}>{message.text}</div>
  )}
</div>

            {message.sources?.length > 0 && (
              <div className="web-sources">
                <strong>Web sources</strong>
                <ul>{message.sources.map((source) => (
                  <li key={source.url}>
                    <a href={source.url} target="_blank" rel="noopener noreferrer" style={{ color: "#7ccfff" }}>{source.title}</a>
                    <small style={{ display: "block", color: "#aaa", marginTop: "4px" }}>{source.page_status === "read" ? "Page excerpt retrieved" : "Search summary only"}{source.date ? ` · ${source.date}` : " · Publication date not provided"}</small>
                  </li>
                ))}</ul>
              </div>
            )}
            {message.searchStatus === "no_results" && <p>No web results found.</p>}

            {message.capability && (
              <div className="message-mode">
                mode: {message.capability}
              </div>
            )}
          </div>
        ))}

        {loading && !streaming && (
          <div
            className="chat-message odb-message thinking" role="status"
          >
            {activity}
          </div>
        )}
      </main>

      <div className="composer-dock">
      {showJump && <button className="jump-latest" onClick={jumpToLatest}>↓ Latest messages</button>}
      <footer className="input-area">
        <textarea
          ref={inputBox}
          aria-label="Message to Shady"
          value={input}
          onChange={(event) =>
            setInput(event.target.value)
          }
          onKeyDown={handleKeyDown}
          placeholder="Talk to ODB..."
          className="message-input"
          rows={1}
        />

        <button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          className="send-button"
        >
          {loading ? "WAIT" : "SEND"}
        </button>
      </footer>
      <div className="composer-hint">Enter adds a new line on your phone · Chats save in this browser</div>
      </div>
    </div>
  );
}
const landingCss = `
.lab-download { display:inline-block; margin-top:12px; padding:10px 16px; border:1px solid #41858a; border-radius:9px; color:#b0f2e9; background:#102a36; font:600 15px Arial,sans-serif; text-decoration:none; }
.lab-download:focus-visible { outline:2px solid #b0f2e9; outline-offset:3px; }
.share-shady { position:relative; }
.share-button { background:#102a36; color:#b0f2e9; border:1px solid #3997a3; border-radius:8px; min-height:42px; padding:8px 12px; font:600 14px Arial,sans-serif; cursor:pointer; }
.share-button:focus-visible { outline:2px solid #b0f2e9; outline-offset:3px; }
.share-notice { position:absolute; right:0; top:calc(100% + 6px); z-index:2; min-width:110px; padding:8px; border-radius:8px; background:#102a36; color:#f1f4f2; font:13px Arial,sans-serif; }
.share-notice input { display:block; width:min(220px,65vw); margin-top:6px; font-size:16px; }
.chat-header { position:relative; z-index:2; }
.chat-menu summary { display:list-item; box-sizing:border-box; padding-top:12px; }
.chat-menu summary:focus-visible { outline:2px solid var(--mint); outline-offset:3px; }
.chat-page .chat-menu .conversation-tools { position:absolute; top:100%; right:12px; box-sizing:border-box; width:min(360px, calc(100% - 24px)); max-height:60dvh; overflow:auto; background:#0a151b; border:1px solid var(--line); border-radius:12px; box-shadow:0 12px 30px #0008; }
.chat-menu .conversation-actions label { order:-1; flex:0 0 100%; min-width:0; }
.chat-menu .conversation-actions select { display:block; width:100%; max-width:100%; margin-top:4px; }
.chat-settings { margin-top:14px; }
.chat-settings .search-control { display:grid; gap:4px; }
.chat-settings select { width:100%; }
.chat-menu .share-shady { margin-top:12px; }
.chat-menu .share-notice { position:static; margin-top:6px; }


.chat-page { --ink:#f1f4f2; --muted:#a8bdc1; --mint:#b0f2e9; --line:#24434b; height:100dvh; height:100svh; height:100dvh; display:flex; flex-direction:column; color:var(--ink); background:radial-gradient(ellipse at 85% 0%,#102a36 0%,#080d10 58%); font-family:Arial,Helvetica,sans-serif; overflow:hidden; }
.chat-header { flex-shrink:0; display:flex; justify-content:space-between; align-items:center; padding:18px 24px; background:#080f14e8; border-bottom:1px solid var(--line); }
.chat-logo { font-size:23px; font-weight:900; letter-spacing:2px; }
.chat-status { font-size:10px; letter-spacing:2px; color:var(--mint); }
.chat-page .lab-back { color:#7cb6cf; letter-spacing:2px; min-height:32px; }
.chat-page .conversation-tools { padding:12px 24px; border-color:var(--line); background:#0a151be0; flex-shrink:0; }
.chat-page .conversation-actions { gap:8px; }
.chat-page .conversation-actions button,.chat-page .conversation-actions select,.search-control select { min-height:42px; background:#10212a; color:#d7ecec; border:1px solid #2b4b57; border-radius:9px; font-size:14px; padding:9px 12px; }
.chat-page .conversation-actions button:first-child { background:#143840; border-color:#41858a; color:var(--mint); }
.chat-page .conversation-tools p { font-size:11px; color:#91aaaf; }
.chat-feed { flex:1; min-height:0; overflow-y:auto; overscroll-behavior:contain; padding:24px max(20px,calc((100% - 860px)/2)); scrollbar-color:#3e6977 #091218; }
.chat-message { box-sizing:border-box; padding:20px; margin:0 0 20px; border-radius:16px; line-height:1.65; min-width:0; max-width:100%; }
.odb-message { margin-right:7%; background:#0d1a21; border:1px solid #24434b; box-shadow:0 8px 32px #0002; }
.user-message { margin-left:12%; background:linear-gradient(135deg,#123440,#102736); border:1px solid #326273; }
.message-role { font:700 10px monospace; letter-spacing:3px; margin-bottom:12px; color:#8dddd7; }
.user-message .message-role { color:#8ec8f1; }
.message-mode { font-size:10px; color:#8ba5ac; margin-top:14px; }
.chat-page .chat-markdown { font-size:16px; overflow-wrap:break-word; }
.chat-page .chat-markdown p:first-child { margin-top:0; }
.chat-page .chat-markdown p:last-child { margin-bottom:0; }
.chat-page .chat-markdown a { color:#8dd8ff; }
.chat-page .chat-markdown h1 { font-size:1.5em; }.chat-page .chat-markdown h2 { font-size:1.3em; }.chat-page .chat-markdown h3 { font-size:1.15em; }
.chat-page .chat-markdown ul,.chat-page .chat-markdown ol { padding-left:24px; }
.chat-page .chat-markdown li { margin:8px 0; }
.chat-page .chat-markdown pre { background:#060e13; border:1px solid #29454e; border-radius:8px; padding:12px; overflow-x:auto; }
.chat-page .chat-markdown pre code { overflow-wrap:normal; white-space:pre; }
.chat-page .chat-markdown img { max-width:100%; height:auto; }
.chat-page .chat-markdown th,.chat-page .chat-markdown td { border-color:#29454e; }
.web-sources { margin-top:20px; border-top:1px solid var(--line); padding-top:14px; font-size:14px; }
.web-sources strong { color:var(--mint); font-size:12px; letter-spacing:1px; }
.web-sources ul { list-style:none; padding:0; margin:10px 0 0; }
.web-sources li { background:#0a141c; border:1px solid #243f49; border-radius:9px; margin:8px 0; padding:12px; overflow-wrap:anywhere; }
.composer-dock { position:relative; flex-shrink:0; border-top:1px solid var(--line); background:#0a141bee; padding:10px max(16px,calc((100% - 860px)/2)) max(10px,env(safe-area-inset-bottom)); }
.search-control { display:flex; align-items:center; gap:10px; color:#a4c1c5; font-size:12px; margin-bottom:10px; }
.search-control select { min-height:36px; padding:5px 10px; font-size:13px; max-width:100%; }
.input-area { display:flex; align-items:flex-end; gap:10px; background:#0e222c; border:1px solid #37616d; border-radius:14px; padding:10px; box-shadow:0 0 24px #1ba6cb0b; }
.input-area:focus-within { border-color:#8dddd7; box-shadow:0 0 0 2px #8dddd71a; }
.message-input { box-sizing:border-box; flex:1; min-width:0; min-height:46px; max-height:180px; overflow-y:auto; resize:none; background:transparent; color:#edf7f6; border:0; padding:12px 8px; font:16px/1.5 Arial,Helvetica,sans-serif; outline:none; }
.message-input::placeholder { color:#8ba6af; }
.send-button { min-height:46px; min-width:70px; border:1px solid #b0f2e9; border-radius:9px; background:#b0f2e9; color:#081817; padding:12px 16px; font-size:12px; font-weight:900; cursor:pointer; }
.send-button:hover:not(:disabled) { background:white; }.send-button:disabled { opacity:.4; cursor:default; }
.composer-hint { padding-top:8px; font-size:10px; color:#819ea6; }
.jump-latest { position:absolute; top:-45px; left:50%; transform:translateX(-50%); border:1px solid #477a86; background:#14313d; color:#c3f3ee; border-radius:20px; padding:9px 16px; white-space:nowrap; cursor:pointer; }
.chat-page button:focus-visible,.chat-page select:focus-visible,.chat-feed:focus-visible { outline:2px solid #8dddd7; outline-offset:3px; }
@media(max-width:650px) {
 .chat-header { padding:12px 16px; }.chat-logo { font-size:19px; letter-spacing:1px; }.chat-status { letter-spacing:1px; }
 .chat-page .conversation-tools { padding:10px 16px; }.conversation-actions label { min-width:0; flex:1; font-size:12px; }.chat-page .conversation-actions select { max-width:100%; width:100%; }
 .chat-page .conversation-actions button { min-height:42px; font-size:12px; padding:9px 11px; }.chat-page .conversation-actions button:first-child { align-self:flex-end; }
 .chat-feed { padding:16px 12px; }.chat-message { padding:16px; margin-bottom:16px; }.odb-message { margin-right:0; }.user-message { margin-left:6%; }
 .composer-dock { padding-left:12px; padding-right:12px; }.search-control select { font-size:16px; }.composer-hint { font-size:9px; }
}

.conversation-tools { padding:14px 20px; border-bottom:1px solid #333; }
.conversation-actions { display:flex; gap:10px; flex-wrap:wrap; align-items:center; }
.conversation-actions button,.conversation-actions select { padding:10px; background:#181818; color:#eee; border:1px solid #555; border-radius:6px; font-size:14px; cursor:pointer; }
.conversation-actions select { max-width: min(65vw, 360px); }
.conversation-actions button:disabled { opacity:.5; cursor:wait; }
.conversation-tools p { margin:10px 0 0; color:#aaa; font-size:12px; }

.chat-markdown a { color:#7ccfff; text-underline-offset:3px; }
.chat-markdown table { min-width:560px; border-collapse:collapse; overflow-wrap:normal; word-break:normal; }
.chat-markdown td,.chat-markdown th { padding:10px; text-align:left; border-bottom:1px solid #444; min-width:130px; }
.chat-markdown p,.chat-markdown li { line-height:1.65; }
@media(max-width:650px) { .chat-markdown { font-size:16px; } }
body { margin: 0; background: #080d10; }
.lab-entrance { min-height: 100svh; position: relative; isolation: isolate; overflow: hidden; background: #080d10; color: #f1f4f2; font-family: Arial, Helvetica, sans-serif; display: flex; flex-direction: column; }
.lab-art { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; object-position: 65% center; z-index: -3; }
.lab-shade { position: absolute; inset: 0; z-index: -2; background: linear-gradient(0deg,rgba(5,12,15,.96),rgba(5,12,15,.55) 35%,transparent 70%); }
.lab-nav { padding: 32px 6vw; display:flex; justify-content:space-between; align-items:center; }
.lab-brand { text-decoration:none; color:inherit; font-weight:900; font-size:28px; letter-spacing:-2px; display:flex; align-items:center; gap:8px; }
.lab-brand b { color:#078bff; } .lab-brand small { font-size:25px; letter-spacing:-1px; margin-left:0; }
.lab-edition { font:11px monospace; letter-spacing:3px; color:#b6c7c9; }
.lab-copy { margin:auto 0 0; padding:180px 6vw 55px; max-width:590px; }
.lab-eyebrow { font:11px monospace; color:#8dddd7; letter-spacing:4px; margin:0 0 30px; }
.lab-copy h1 { font-size:clamp(46px,5vw,72px); line-height:1.01; letter-spacing:-5px; margin:0 0 28px; font-weight:800; }
.lab-copy h1 span { color:#a5b4b5; }
.lab-intro { max-width:350px; color:#b7c6c8; font-size:17px; line-height:1.7; margin-bottom:32px; }
.lab-enter { background:#b0f2e9; border:1px solid #b0f2e9; color:#081817; padding:20px 24px; border-radius:3px; font-size:14px; font-weight:700; cursor:pointer; display:flex; gap:32px; align-items:center; transition:background .2s,transform .2s; }
.lab-enter:hover { background:white; transform:translateY(-2px); } .lab-enter:focus-visible,.lab-back:focus-visible,.lab-brand:focus-visible { outline:3px solid #fff; outline-offset:6px; }
.lab-enter span { font-size:22px; } .lab-hint { font-size:11px; color:#869b9e; margin-top:16px; }
.lab-footer { display:flex; justify-content:space-between; padding:24px 6vw; border-top:1px solid #ffffff1c; font:9px monospace; letter-spacing:2px; color:#8da3a5; }
.lab-back { background:none; border:0; color:#aaa; padding:8px 0 0; font-size:11px; letter-spacing:3px; cursor:pointer; }
@media(max-width:650px) { .lab-nav { padding:24px; } .lab-brand small { font-size:32px; letter-spacing:-1px; margin-left:0; } .lab-edition { font-size:9px; letter-spacing:1px; } .lab-art { top:80px; height:auto; aspect-ratio:2 / 1; object-position:center; } .lab-shade { background:linear-gradient(0deg,#080d10 25%,transparent 65%); } .lab-copy { margin:auto 0 0; padding:calc(50vw + 35px) 24px 40px; } .lab-copy h1 { font-size:52px; letter-spacing:-2.5px; } .lab-eyebrow { margin-bottom:20px; } .lab-intro { font-size:15px; } .lab-footer { padding:20px 24px; font-size:8px; } .lab-footer span:last-child { display:none; } }
@media(prefers-reduced-motion:reduce) { .lab-enter { transition:none; } }
`;
