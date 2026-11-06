# Chat attachments

The paperclip accepts up to three files per message, each at most 2 MiB.
Supported: JPEG/PNG/WebP photos, readable unencrypted PDFs (up to ten pages), UTF-8 text, Markdown, CSV, JSON, and common code files. Audio, video, Office documents, and archives are rejected with an explanation.

Deploy frontend and backend together; install the updated backend requirements (pypdf). Photo reading uses the existing server-side GROQ_API_KEY and GROQ_VISION_MODEL, default qwen/qwen3.8-27b. Enable access to this model in Groq if your project restricts model access. Photo requests incur vision model usage. The vision description and document excerpts are marked as untrusted reference data before being supplied to Shady. Large document excerpts are bounded and marked as truncated.

Uploads are sent with the current message. Saved chats retain filenames and the resulting reply, not the original attachment bytes. Reattach files when their contents are needed in a later message. Files are processed in memory and passed to the configured AI provider; they are not uploaded to a public URL.

Android version 1.0.1 includes the native file picker and print dialog. Users of version 1.0.0 must install the updated signed APK from the download page. Browser users receive the picker with the web deployment. iOS uses the browser document/photo picker. No camera, microphone, or broad storage permission is requested by the Android wrapper.

Validation: attachment decoding, invalid formats, limits, context bounding, mocked vision submission/failure, existing image generation tests, and frontend production build. Real-device selection and live vision inference still require deployment testing.

# Printing

Menu > Print chat opens the browser print dialog or, in the updated Android wrapper, Android PrintManager. The user chooses their configured printer or Save as PDF. This prints the current conversation, including generated images; it does not send a print job automatically. The print stylesheet expands the scrolling chat, hides the composer and controls, wraps code, and fits tables onto the page. A printer must already be available through the device's print service.
