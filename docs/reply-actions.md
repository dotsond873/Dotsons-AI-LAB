# Reply actions

Completed, successful assistant replies show thumbs up/down, Copy, Share, and a Sources globe button. Greetings, incomplete streams, and failed replies omit the row.

Ratings toggle on/off, are mutually exclusive, and persist with the saved conversation on the current device. They are not sent to the owner or used for automatic model training.

Copy includes the reply text, generated-image description when present, and source URLs. Clipboard failures expose selectable text. Share opens the browser share sheet or the Android native text share chooser in version 1.0.2. Older Android wrappers and browsers without sharing fall back to copying/selectable text. This shares reply text and links, not generated-image files.

Sources toggles the specific reply's retrieved sources, with a clear empty state for replies without web evidence. It never creates citations for unsourced answers.

Deploy the frontend to expose the controls. Install the updated signed Android APK for native text sharing. Checks: production web build, rating persistence/removal, Android compile/lint and APK signature validation. Device share sheet and clipboard behavior still require phone testing.
