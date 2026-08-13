import { useState } from "react";

const API_URL = "https://dotsons-ai-lab.onrender.com";

export default function App() {
  const [provider, setProvider] = useState("openai");
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
        setResponse(data.detail || "Request failed.");
      } else {
        setResponse(data.response);
      }
    } catch (error) {
      setResponse("Could not connect to Dotsons AI LAB.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <h1>DOTSONS AI LAB</h1>
      <p>One AI Lab. Multiple AI Engines.</p>

      <select
        value={provider}
        onChange={(e) => setProvider(e.target.value)}
      >
        <option value="openai">GPT</option>
        <option value="claude">Claude</option>
        <option value="gemini">Gemini</option>
        <option value="grok">Grok</option>
      </select>

      <textarea
        placeholder="Ask anything..."
        value={message}
        onChange={(e) => setMessage(e.target.value)}
      />

      <button onClick={sendMessage} disabled={loading}>
        {loading ? "Thinking..." : "Send"}
      </button>

      {response && (
        <section>
          <strong>{provider.toUpperCase()}</strong>
          <p>{response}</p>
        </section>
      )}
    </main>
  );
}