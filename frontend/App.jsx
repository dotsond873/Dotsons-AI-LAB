import { useState } from "react";

const API_URL = "https://dotsons-ai-lab.onrender.com";

export default function App() {
  const [provider, setProvider] = useState("claude");
  const [message, setMessage] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);

  async function sendMessage() {
    if (!message.trim()) return;

    setLoading(true);
    setResponse("");

    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message,
          provider,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Request failed");
      }

      setResponse(data.response);
    } catch (error) {
      setResponse(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <header>
        <h1>Dotsons AI Lab</h1>
        <p>Multiple AI models. One powerful workspace.</p>
      </header>

      <main>
        <label htmlFor="provider">Choose AI</label>

        <select
          id="provider"
          value={provider}
          onChange={(e) => setProvider(e.target.value)}
        >
          <option value="claude">Claude</option>
          <option value="gemini">Gemini</option>
          <option value="openai">ChatGPT</option>
          <option value="grok">Grok</option>
        </select>

        <textarea
          placeholder="Ask anything..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          rows="7"
        />

        <button onClick={sendMessage} disabled={loading}>
          {loading ? "Thinking..." : "Send"}
        </button>

        {response && (
          <section className="response">
            <h2>Response</h2>
            <p>{response}</p>
          </section>
        )}
      </main>
    </div>
  );
}