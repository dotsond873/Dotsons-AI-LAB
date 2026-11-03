export async function readAnswerStream(response, onEvent) {
  if (!response.body) throw new Error("Streaming is unavailable in this browser.");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "", complete = false;
  function line(value) {
    if (!value.trim()) return;
    const data = JSON.parse(value);
    if (data.type === "error") throw new Error(data.message || "Response interrupted.");
    onEvent(data);
    if (data.type === "done") complete = true;
  }
  try {
    while (!complete) {
      const { value, done } = await reader.read();
      buffer += done ? decoder.decode() : decoder.decode(value, { stream:true });
      let boundary;
      while ((boundary = buffer.indexOf("\n")) !== -1) {
        const record = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 1);
        line(record);
        if (complete) break;
      }
      if (done) {
        if (!complete && buffer.trim()) line(buffer);
        break;
      }
    }
    if (!complete) throw new Error("The connection ended before Shady finished.");
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}
