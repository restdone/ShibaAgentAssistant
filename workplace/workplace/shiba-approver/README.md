# Shiba Approver — Android App

Receives approval requests from Shiba (write file / execute command) over your local WiFi and lets you approve or reject them from your phone.

---

## How it works

1. When Shiba is about to write a file or run a command, it posts the request to a local Flask server running on this machine (port 7845).
2. The Android app polls that server every 2 seconds.
3. When a request arrives, a high-priority notification fires.
4. Tap the notification → full detail screen → Approve or Reject.
5. The decision is sent back to the server, and Shiba proceeds or cancels.

---

## Building the APK

You need the **Android command line tools** (or Android Studio) on any machine.

### Option A — Android Studio
1. Open this folder as a project.
2. Let it sync Gradle.
3. Build → Build Bundle(s) / APK(s) → Build APK(s).
4. APK lands at `app/build/outputs/apk/debug/app-debug.apk`.

### Option B — Command line tools only

Install the Android command line tools:
```
# On macOS (Homebrew)
brew install --cask android-commandlinetools

# On Ubuntu/Debian
sudo apt install android-sdk
# or download from https://developer.android.com/studio#command-line-tools-only
```

Accept licenses:
```
sdkmanager --licenses
sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"
```

Then build:
```
cd shiba-approver
./gradlew assembleDebug
```

APK output: `app/build/outputs/apk/debug/app-debug.apk`

Install directly to a connected phone:
```
adb install app/build/outputs/apk/debug/app-debug.apk
```

---

## First-time setup on the phone

1. Open the app.
2. Enter your machine's local IP (find it with `ip addr` or `hostname -I` on the machine).
3. Port is `7845` by default.
4. Tap **Test Connection** — should say "Connected".
5. Tap **Start Polling**.

The app will restart polling automatically on phone reboot.
