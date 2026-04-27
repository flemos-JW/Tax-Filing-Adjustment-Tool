# Tax Filing Adjustment Bulk Upload Tool

A Streamlit app for matching names to MIDs and generating tax filing adjustment bulk upload files.

---

## One-Time Setup

### 1. Install Python
Download and install Python from [python.org/downloads](https://www.python.org/downloads/). Choose the latest version and run the installer.

To verify it installed, open **Terminal** and run:
```
python3 --version
```

### 2. Clone the repo
In Terminal, run:
```
git clone https://github.com/flemos-JW/Tax-Filing-Adjustment-Tool.git
cd Tax-Filing-Adjustment-Tool
```

### 3. Install dependencies
```
pip3 install -r requirements.txt
```

---

## Running the App

Any time you want to open the app, run this in Terminal:
```
streamlit run name_to_mid.py
```
The app will open automatically in your browser at `http://localhost:8504`.

---

## Auto-Launch on Startup (Mac)

Follow these steps once to have the app start automatically every time you turn on your Mac.

### 1. Find your username
In Terminal, run:
```
whoami
```
Note the output — it's your Mac username (e.g. `janesmith`).

### 2. Find the full path to Python
In Terminal, run:
```
which python3
```
Note the output (e.g. `/usr/local/bin/python3`).

### 3. Create the launch agent file
Open TextEdit, switch to plain text mode (**Format → Make Plain Text**), and paste the following — replacing `YOUR_USERNAME`, `YOUR_PYTHON_PATH`, and `YOUR_REPO_PATH` with your actual values:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.YOUR_USERNAME.taxfilingtool</string>

    <key>ProgramArguments</key>
    <array>
        <string>YOUR_PYTHON_PATH</string>
        <string>-m</string>
        <string>streamlit</string>
        <string>run</string>
        <string>/Users/YOUR_USERNAME/YOUR_REPO_PATH/name_to_mid.py</string>
        <string>--server.headless</string>
        <string>true</string>
        <string>--server.port</string>
        <string>8504</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/Users/YOUR_USERNAME/Library/Logs/taxfilingtool.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USERNAME/Library/Logs/taxfilingtool.log</string>
</dict>
</plist>
```

Save the file as `com.YOUR_USERNAME.taxfilingtool.plist` in this folder:
```
/Users/YOUR_USERNAME/Library/LaunchAgents/
```

### 4. Register the launch agent
In Terminal, run:
```
launchctl load ~/Library/LaunchAgents/com.YOUR_USERNAME.taxfilingtool.plist
```

The app will now start automatically on login and restart if it ever crashes. Access it at `http://localhost:8504`.

### To stop the auto-launch
```
launchctl unload ~/Library/LaunchAgents/com.YOUR_USERNAME.taxfilingtool.plist
```
