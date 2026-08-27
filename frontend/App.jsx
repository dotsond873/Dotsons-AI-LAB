import { useState } from "react";

const API_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "ODB SHADY 6.9 online. What kind of trouble are we getting into?",
    },
  ]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

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

  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <div>
          <div style={styles.logo}>
            ODB SHADY 6.9
          </div>

          <div style={styles.subtitle}>
            DOTSON LABS
          </div>
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

            <div>{message.text}</div>

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
