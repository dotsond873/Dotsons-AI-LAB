# Shady Android

This Android app opens the production HTTPS Shady frontend in a WebView, with
local chat storage, external links in the browser, and connection retry controls.
The backend remains hosted on Render. Internet access is required.

## Release setup

Add one GitHub Actions repository secret named `SHADY_ANDROID_SIGNING_JSON`.
Its JSON value contains `keystore` (base64 of the private JKS signing file) and
`password` (the store and key password). The keystore alias must be `shady`.
Keep the same signing key for all updates and retain a private backup.
Never commit this secret to the repository.

Run **Build Shady Android** under Actions. It compiles and lints the app, signs
and verifies `Shady.apk`, then publishes it with a checksum in a GitHub release.
The website's `/download.html` page finds the newest Android release and falls
back to the bundled first installer at `/downloads/Shady.apk`.
Compilation runs before the signing configuration check, so a missing secret
still permits build validation but prevents publication.

The app ID is `com.dotsonlabs.shady`. Release version codes follow the workflow
run number plus 1000, above the bundled first installer's version code of 1.
Re-run a failed job after adding the signing secret.

## Local build

Use JDK 17, Gradle 8.13, Android platform 36, and build tools 35.0.0.
From this directory run `gradle :app:assembleRelease :app:lintRelease`.
The output requires signing before installation.

Google/GitHub account sign-in and owner-only sharing are pending separate
authentication work. This wrapper does not add an account system.
