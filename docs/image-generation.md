# Image creation

Shady creates one 1024×1024 JPEG per request through the OpenAI Images API.
Use **Menu → Create image**, type `/image a robot working in Dotson Labs`,
or ask directly, for example `Generate an image of a robot working in a lab`.
Image requests bypass the text provider and web search. Streamed requests
send progress events while waiting and show the image inside the chat reply.

## Backend configuration on Render

- `OPENAI_API_KEY` — a server-side OpenAI API key with image-model access and API billing.
- `IMAGE_GENERATION_ENABLED=true` — explicitly activates billed image requests.
- `OPENAI_IMAGE_MODEL` — optional, defaults to `gpt-image-2.5-sunburst`.

The feature stays disabled until both the key and activation setting exist.
Do not put the key in any `VITE_` variable or frontend source.
`/health` reports image configuration booleans and the model, without exposing the key.
The OpenAI account's access and billing must be checked with a real generation
after deploying. Mocked tests do not establish that the account can use the model.
Only one image request runs at a time per backend process. The existing app's
owner sign-in and account authorization are separate pending work. This
concurrency limit is not an authentication or spending-limit system.

## Saved images

JPEG blobs are saved in IndexedDB on the current browser or installed Android
app. Saved-chat JSON contains image IDs and descriptions rather than base64
data, so images do not fill localStorage. Deleting a conversation also removes
its saved image blobs. If image storage is unavailable, the image stays visible
in the current tab with a warning. Clearing application/browser data removes
saved images. Text history includes the image's description, not its pixels.
This feature creates new images from text. Image editing and uploaded-image
understanding require separate implementation.

Deploy backend and frontend. The Android wrapper loads the live frontend.
Test generation, progress, reopening a saved chat, deleting a chat, and an
upstream provider failure. Automated checks use mocked provider responses.
