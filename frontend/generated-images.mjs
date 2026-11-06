const previews = new Map();

function imageStore(mode, operation) {
  return new Promise((resolve, reject) => {
    const opening = indexedDB.open("shady-generated-images", 1);
    opening.onupgradeneeded = () => opening.result.createObjectStore("images");
    opening.onerror = () => reject(opening.error);
    opening.onblocked = () => reject(new Error("Image storage is blocked."));
    opening.onsuccess = () => {
      const db = opening.result;
      db.onversionchange = () => db.close();
      try {
        const transaction = db.transaction("images", mode);
        const request = operation(transaction.objectStore("images"));
        transaction.oncomplete = () => { db.close(); resolve(request?.result); };
        transaction.onabort = () => { db.close(); reject(transaction.error); };
        transaction.onerror = () => { db.close(); reject(transaction.error); };
      } catch (error) { db.close(); reject(error); }
    };
  });
}

export async function saveGeneratedImage(image) {
  if (image.mime_type !== "image/jpeg" || typeof image.data !== "string" || image.data.length > 12000000) {
    throw new Error("Shady received an invalid image.");
  }
  const bytes = Uint8Array.from(atob(image.data), character => character.charCodeAt(0));
  const blob = new Blob([bytes], { type: "image/jpeg" });
  const metadata = { id: crypto.randomUUID(), prompt: image.prompt || "Generated image", model: image.model, saved: true };
  previews.set(metadata.id, blob);
  try {
    await imageStore("readwrite", store => store.put(blob, metadata.id));
  } catch {
    metadata.saved = false;
  }
  return metadata;
}

export async function loadGeneratedImage(id) {
  return previews.get(id) || await imageStore("readonly", store => store.get(id));
}

export async function deleteGeneratedImages(messages) {
  const ids = messages.filter(message => message.image).map(message => message.image.id);
  ids.forEach(id => previews.delete(id));
  if (!ids.length) return;
  try {
    await imageStore("readwrite", store => {
      for (const id of ids) store.delete(id);
    });
  } catch { /* A failed cleanup must not block deleting the conversation. */ }
}
