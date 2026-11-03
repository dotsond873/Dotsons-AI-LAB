
import { useState } from "react";
import labArt from "./assets/odb-lab-v2.webp";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
const API_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [entered, setEntered] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "ODB SHADY 6.9 online. What kind of trouble are we getting into?",
    },
  ]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [webSearch, setWebSearch] = useState(null);

  const sessionId = "odb-default-session";

  async function sendMessage() {
    const text = input.trim();

    if (!text || loading) return;

    setMessages((old) => [
      ...old,
      {
        role: "user",
        text,
      },
    ]);

    setInput("");
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/chat`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    message: text,
    session_id: sessionId,
    web_search: webSearch,
  }),
});

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "ODB backend returned an error."
        );
      }

      setMessages((old) => [
        ...old,
        {
          role: "assistant",
          text: data.response,
          capability: data.capability,
          sources: data.sources || [],
          searchStatus: data.search_status,
        },
      ]);
    } catch (error) {
      setMessages((old) => [
        ...old,
        {
          role: "assistant",
          text:
            "ODB backend connection failed: " +
            error.message,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
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
        <span className="lab-edition">ODB / 6.9</span>
      </nav>
      <section className="lab-copy" id="home">
        <p className="lab-eyebrow">WELCOME TO THE LAB</p>
        <h1>Intelligence.<br /><span>With attitude.</span></h1>
        <p className="lab-intro">Meet ODB SHADY 6.9. Your space to ask questions, explore ideas, and search the web.</p>
        <button className="lab-enter" onClick={() => { setEntered(true); window.scrollTo(0, 0); }}>Enter ODB SHADY 6.9 <span aria-hidden="true">↗</span></button>
        <p className="lab-hint">Step inside. Bring your curiosity.</p>
      </section>
      <footer className="lab-footer"><span>DOTSON LABS / ARTIFICIAL INTELLIGENCE</span><span>ASK. EXPLORE. CREATE.</span></footer>
    </main>
  );

  return (
    <div style={styles.page}>
      <style>{landingCss}</style>
      <header style={styles.header}>
        <div>
          <div style={styles.logo}>
            ODB SHADY 6.9
          </div>

          <button className="lab-back" onClick={() => setEntered(false)}>← DOTSON LABS</button>
        </div>

        <div style={styles.status}>
          ● ONLINE
        </div>
      </header>

      <main style={styles.chat}>
        {messages.map((message, index) => (
          <div
            key={index}
            style={{
              ...styles.message,
                            ...(message.role === "user"
                ? styles.userMessage
                : styles.odbMessage),
            }}
          >
            <div style={styles.role}>
              {message.role === "user"
                ? "YOU"
                : "ODB"}
            </div>

            <div style={{ whiteSpace: "normal", overflowWrap: "anywhere" }}>
  {message.role === "assistant" ? (
    <div className="chat-markdown" style={{ overflowX: "auto" }}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {message.text}
      </ReactMarkdown>
    </div>
  ) : (
    <div style={{ whiteSpace: "pre-wrap" }}>{message.text}</div>
  )}
</div>

            {message.sources?.length > 0 && (
              <div>
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
              <div style={styles.capability}>
                mode: {message.capability}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div
            style={{
              ...styles.message,
              ...styles.odbMessage,
            }}
          >
            ODB is thinking...
          </div>
        )}
      </main>

      <label style={{ padding: "12px 20px" }}>
        Web search:{" "}
        <select aria-label="Web search mode" value={webSearch === null ? "auto" : webSearch ? "on" : "off"} disabled={loading}
          onChange={(event) => setWebSearch(event.target.value === "auto" ? null : event.target.value === "on")}
          style={{ background: "#181818", color: "white", padding: "8px", border: "1px solid #555", borderRadius: "6px", fontSize: "16px" }}>
          <option value="auto">Auto — search when needed</option>
          <option value="on">Always search</option>
          <option value="off">Search off</option>
        </select>
      </label>
      <footer style={styles.inputArea}>
        <textarea
          value={input}
          onChange={(event) =>
            setInput(event.target.value)
          }
          onKeyDown={handleKeyDown}
          placeholder="Talk to ODB..."
          style={styles.input}
          rows={2}
        />

        <button
          onClick={sendMessage}
          disabled={loading}
          style={styles.button}
        >
          SEND
        </button>
      </footer>
    </div>
  );
}
const styles = {
  page: {
    minHeight: "100vh",
    background:
      "linear-gradient(180deg, #090909, #151515)",
    color: "#f5f5f5",
    fontFamily: "Arial, Helvetica, sans-serif",
    display: "flex",
    flexDirection: "column",
  },

  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "20px",
    borderBottom: "1px solid #333",
    background: "#050505",
  },

  logo: {
    fontSize: "28px",
    fontWeight: "900",
    letterSpacing: "2px",
  },

  subtitle: {
    fontSize: "11px",
    color: "#888",
    letterSpacing: "4px",
    marginTop: "4px",
  },

  status: {
    fontSize: "12px",
    color: "#7cff8a",
    fontWeight: "bold",
  },

  chat: {
    flex: 1,
    width: "100%",
    maxWidth: "900px",
    margin: "0 auto",
    padding: "20px",
    boxSizing: "border-box",
  },

  message: {
    padding: "15px",
    marginBottom: "14px",
    borderRadius: "14px",
    lineHeight: "1.5",
    whiteSpace: "pre-wrap",
  },
    userMessage: {
    marginLeft: "15%",
    background: "#292929",
    border: "1px solid #444",
  },

  odbMessage: {
    marginRight: "15%",
    background: "#111",
    border: "1px solid #333",
  },

  role: {
    fontSize: "11px",
    fontWeight: "bold",
    letterSpacing: "2px",
    marginBottom: "8px",
    color: "#aaa",
  },

  capability: {
    fontSize: "10px",
    color: "#777",
    marginTop: "10px",
  },

  inputArea: {
    display: "flex",
    gap: "10px",
    padding: "16px",
    borderTop: "1px solid #333",
    background: "#050505",
  },

  input: {
    flex: 1,
    resize: "none",
    background: "#181818",
    color: "white",
    border: "1px solid #444",
    borderRadius: "10px",
    padding: "12px",
    fontSize: "16px",
    outline: "none",
  },

  button: {
    background: "#f2f2f2",
    color: "#111",
    border: "none",
    borderRadius: "10px",
    padding: "0 22px",
    fontWeight: "900",
    cursor: "pointer",
  },
};

const landingCss = `
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
