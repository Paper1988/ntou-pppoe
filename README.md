# NTOU PPPoE

一個專為 **國立臺灣海洋大學（NTOU）宿舍 PPPoE 網路**設計的 Windows 自動連線與網路管理工具。

NTOU PPPoE 使用 Windows 內建的 Remote Access Service（RAS）管理 PPPoE 連線，並持續監控目前的網路狀態。當連線中斷或健康檢查失敗時，程式會自動嘗試恢復連線。

> 💡 本專案主要提供給海大宿舍使用者使用，也歡迎其他需要 Windows PPPoE 自動管理功能的人使用。

---

## ✨ 功能

### 🔌 PPPoE 自動連線

啟動服務後，程式會自動連線到指定的 Windows PPPoE 連線。

程式會確認 Windows RAS 回報連線成功，並進一步確認實際 PPPoE connection 是否已建立。

### 🔄 自動重新連線

程式會定期檢查目前的網路狀態。

當偵測到以下任一項異常：

- PPPoE 連線消失
- IPv4 位址消失
- Default Gateway 不存在
- DNS 無法解析
- HTTPS 無法連線

程式會進入 recovery 流程並嘗試重新建立 PPPoE 連線。

重新連線使用 **Exponential Backoff（指數退避）**，避免網路異常時持續高速重試。

### 🩺 多層網路健康檢查

每次健康檢查會確認：

```text
PPPoE
  ↓
IPv4
  ↓
Default Gateway
  ↓
DNS
  ↓
HTTPS
```

只有全部檢查通過時，才會將目前連線判定為健康。

### 📊 Terminal Dashboard

CLI 指令會顯示目前：

- PPPoE 狀態
- IPv4
- Default Gateway
- DNS Server
- 網路健康檢查結果
- Retry 次數

### 🪟 Windows 自動啟動

可以透過 Windows Task Scheduler 安裝自動啟動工作。

使用者登入 Windows 後，程式會在背景自動啟動，不需要手動開啟 CMD。

Task Scheduler 使用 `pythonw.exe` 執行，因此正常啟動時不會額外開啟 Python 主控台視窗。

### 📝 日誌

程式會將服務執行狀況寫入：

```text
logs/ntou-pppoe.log
```

並使用 rotating log，避免 log 檔案無限制增長。

---

# English

NTOU PPPoE is a Windows PPPoE connection manager designed primarily for the **National Taiwan Ocean University (NTOU) dormitory network**.

It uses the Windows built-in Remote Access Service (RAS) API to establish, monitor, and recover PPPoE connections.

The application continuously monitors the network and automatically attempts to recover the connection when the PPPoE session or Internet connectivity becomes unavailable.

> 💡 The project is primarily intended for NTOU dormitory users, but it can also be used by other Windows users who need automatic PPPoE connection management.

## ✨ Features

### 🔌 Automatic PPPoE Connection

When the service starts, NTOU PPPoE automatically connects to the configured Windows PPPoE profile.

The application does not simply trust the return value from the RAS API. After a successful dial operation, it verifies that the PPPoE connection is actually active.

### 🔄 Automatic Reconnection

The application periodically monitors the current network state.

Recovery can be triggered when any of the following checks fail:

- The PPPoE connection disappears
- No IPv4 address is available
- No default gateway is detected
- DNS resolution fails
- HTTPS connectivity fails

When a failure is detected, the connection manager enters its recovery process and attempts to establish the PPPoE connection again.

Recovery attempts use **exponential backoff** to avoid repeatedly reconnecting at a high frequency during network failures.

### 🩺 Multi-Layer Network Health Checks

Each health-check cycle evaluates several layers of the network connection:

```text
PPPoE
  ↓
IPv4
  ↓
Default Gateway
  ↓
DNS
  ↓
HTTPS
```

The connection is considered fully healthy only when all five checks pass.

The five checks are:

| Check   | Description                                                 |
| ------- | ----------------------------------------------------------- |
| PPPoE   | Verifies that the configured RAS PPPoE connection is active |
| IPv4    | Verifies that an IPv4 address is available                  |
| Gateway | Verifies that a default gateway is present                  |
| DNS     | Verifies that the configured hostname can be resolved       |
| HTTPS   | Verifies that an HTTPS request can reach the configured URL |

### 📊 Terminal Dashboard

The CLI provides a compact terminal dashboard showing the current:

- Connection state
- PPPoE profile
- IPv4 address
- Default gateway
- DNS servers
- Network health
- Individual health-check results
- Retry attempt count

For example:

```text
╭──── NTOU PPPoE Manager ────╮
│ Status    ● Connected       │
│ Profile   NTOU-PPPoE        │
│ IPv4      118.xxx.xxx.xxx   │
│ Gateway   26.xxx.xxx.xxx    │
│ DNS       168.95.xxx.xxx    │
│ Health    █████ 5/5         │
│ Checks    ✓ ✓ ✓ ✓ ✓         │
│ Retry     0                 │
╰─────────────────────────────╯
```

### 🪟 Windows Automatic Startup

The project includes scripts for integrating the service with Windows Task Scheduler.

After installation, the scheduled task starts the manager when the user logs into Windows.

The scheduled task launches the application through `pythonw.exe`, allowing the service to run in the background without opening a Python console window.

### 📝 Logging

Application logs are written to:

```text
logs/ntou-pppoe.log
```

Logs use a rotating file handler to prevent the log file from growing indefinitely.

---

# 🖥️ 使用需求

## 作業系統

- Windows 10
- Windows 11

## Python

需要 Python **3.11 或更新版本**。

可以使用：

```powershell
python --version
```

確認目前 Python 版本。

## Windows PPPoE 連線

使用本程式前，必須先在 Windows 中建立 PPPoE 連線，並確認可以正常手動連線。

本程式負責管理已存在的 Windows PPPoE connection，不負責申請網路服務或建立帳號。

## PPPoE 帳號密碼

PPPoE 帳號與密碼由 Windows 的 PPPoE/RAS connection 管理。

**請不要把 PPPoE 密碼寫入本專案的 `config.json`。**

---

# English Requirements

## Operating System

- Windows 10
- Windows 11

## Python

Python **3.11 or newer** is required.

Check your installed version with:

```powershell
python --version
```

## Windows PPPoE Connection

A Windows PPPoE connection must already exist before using this application.

You should verify that the connection can be established manually through Windows before installing the automatic connection manager.

This project manages an existing Windows PPPoE profile. It does not create network accounts or provide Internet service.

## PPPoE Credentials

PPPoE credentials are managed by Windows through the configured PPPoE/RAS connection.

**Do not store your PPPoE password in `config.json`.**

---

# 🚀 安裝

## 1. 建立 Windows PPPoE 連線

請先使用 Windows 的網路設定建立 PPPoE 連線。

建立完成後，確認可以透過 Windows 手動連線。

例如本專案可以使用：

```text
NTOU-PPPoE
```

作為 Windows connection name。

你的連線名稱可以不同。

> ⚠️ `connection_name` 必須與 Windows 中實際存在的 PPPoE 連線名稱完全一致。

## 2. 下載專案

Clone repository：

```powershell
git clone https://github.com/Paper1988/ntou-pppoe
cd ntou-pppoe
```

也可以直接下載 GitHub ZIP，解壓縮後進入專案資料夾。

## 3. 安裝 Python package

在專案根目錄執行：

```powershell
python -m pip install -e .
```

再安裝 requirements：

```powershell
python -m pip install -r requirements.txt
```

安裝完成後，可以確認程式是否能正常啟動：

```powershell
python -m ntou_pppoe --help
```

## 4. 建立設定檔

複製範例設定：

```powershell
Copy-Item config\config.example.json config\config.json
```

然後編輯：

```text
config/config.json
```

範例：

```json
{
    "connection_name": "NTOU-PPPoE",
    "startup_delay": 5,
    "check_interval": 30,
    "connect_timeout": 30,
    "health_check": {
        "enabled": true,
        "dns_host": "example.com",
        "https_url": "https://www.example.com",
        "timeout": 5
    },
    "retry": {
        "initial_delay": 5,
        "max_delay": 60,
        "max_attempts": 5
    }
}
```

最重要的是：

```json
"connection_name": "NTOU-PPPoE"
```

請將它改成你的 Windows PPPoE connection name。

### 🔐 安全性注意事項

`config/config.json` 已經被加入 `.gitignore`，因此不會被 Git 加入 repository。

請不要將包含私人資訊的設定檔、帳號密碼或其他敏感資料提交到 GitHub。

## 5. 測試手動連線

完成設定後，可以先測試：

```powershell
python -m ntou_pppoe connect
```

如果成功，程式會顯示 PPPoE connection、IPv4、Gateway、DNS 和健康檢查結果。

如果目前已經連線，程式會偵測現有 connection，不會重複建立連線。

## 6. 安裝 Windows 自動啟動

確認手動連線正常後，可以安裝 Task Scheduler：

```powershell
scripts\install.bat
```

安裝程式需要系統管理員權限。

Windows 會建立：

```text
NTOU-PPPoE Manager
```

這個 scheduled task。

預設啟動流程：

```text
Windows User Logon
        ↓
Task Scheduler
        ↓
pythonw.exe
        ↓
NTOU PPPoE Manager
```

之後登入 Windows 時，程式會自動在背景啟動。

---

# English Installation

## 1. Create a Windows PPPoE Connection

First create and configure your PPPoE connection through Windows.

Make sure the connection can be established manually before installing NTOU PPPoE.

For example, the Windows connection profile may be named:

```text
NTOU-PPPoE
```

Your profile name may be different.

> ⚠️ The `connection_name` value must exactly match the PPPoE profile name configured in Windows.

## 2. Clone the Repository

```powershell
git clone <repository-url>
cd ntou-pppoe
```

You may also download the repository as a ZIP archive and extract it locally.

## 3. Install the Python Package

From the project root:

```powershell
python -m pip install -e .
```

Install the required dependencies:

```powershell
python -m pip install -r requirements.txt
```

Verify that the application can start:

```powershell
python -m ntou_pppoe --help
```

## 4. Create the Configuration File

Copy the example configuration:

```powershell
Copy-Item config\config.example.json config\config.json
```

Then edit:

```text
config/config.json
```

Example:

```json
{
    "connection_name": "NTOU-PPPoE",
    "startup_delay": 5,
    "check_interval": 30,
    "connect_timeout": 30,
    "health_check": {
        "enabled": true,
        "dns_host": "example.com",
        "https_url": "https://www.example.com",
        "timeout": 5
    },
    "retry": {
        "initial_delay": 5,
        "max_delay": 60,
        "max_attempts": 5
    }
}
```

The most important option is:

```json
"connection_name": "NTOU-PPPoE"
```

Change it to the name of your Windows PPPoE connection.

### 🔐 Security

`config/config.json` is included in `.gitignore` and should not be committed to the repository.

Do not upload configuration files containing private information, credentials, or other sensitive data to GitHub.

## 5. Test the Connection

Run:

```powershell
python -m ntou_pppoe connect
```

If successful, the application will display the PPPoE state, IPv4 address, gateway, DNS servers, and network health.

If the connection is already active, the application detects the existing RAS connection instead of creating a duplicate connection.

## 6. Install Windows Automatic Startup

After verifying that manual connection works, run:

```powershell
scripts\install.bat
```

Administrator privileges are required to install the scheduled task.

The installer creates:

```text
NTOU-PPPoE Manager
```

in Windows Task Scheduler.

The default startup flow is:

```text
Windows User Logon
        ↓
Task Scheduler
        ↓
pythonw.exe
        ↓
NTOU PPPoE Manager
```

The service will then start automatically in the background whenever the configured Windows user logs in.

---

# 🎮 使用方式

所有 CLI 指令都可以透過：

```powershell
python -m ntou_pppoe <command>
```

執行。

## 啟動服務

```powershell
python -m ntou_pppoe start
```

服務會持續執行：

```text
啟動
 ↓
等待 startup_delay
 ↓
建立 PPPoE
 ↓
確認連線
 ↓
健康檢查
 ↓
等待 check_interval
 ↓
再次健康檢查
 ↓
正常 → 繼續監控
 ↓
異常 → Recovery
 ↓
重新連線
```

這是安裝 Task Scheduler 後主要使用的模式。

## Connect

```powershell
python -m ntou_pppoe connect
```

手動建立 PPPoE 連線。

成功後會執行完整網路健康檢查並顯示診斷資訊。

## Disconnect

```powershell
python -m ntou_pppoe disconnect
```

手動中斷 PPPoE 連線。

程式會等待並確認 PPPoE connection 實際消失。

## Status

```powershell
python -m ntou_pppoe status
```

查看目前連線狀態。

會顯示：

- Connection State
- PPPoE
- IPv4
- Gateway
- DNS
- HTTPS
- Retry

## Diagnose

```powershell
python -m ntou_pppoe diagnose
```

取得目前網路診斷資訊：

- IPv4 address
- Default Gateway
- DNS servers

此指令主要用於排查網路問題。

---

# English Usage

All CLI commands use the following format:

```powershell
python -m ntou_pppoe <command>
```

## Start the Service

```powershell
python -m ntou_pppoe start
```

The service continuously monitors the connection:

```text
Start
 ↓
Wait for startup_delay
 ↓
Establish PPPoE
 ↓
Verify connection
 ↓
Run health check
 ↓
Wait for check_interval
 ↓
Run another health check
 ↓
Healthy → Continue monitoring
 ↓
Unhealthy → Recovery
 ↓
Reconnect
```

This is the primary mode used by the Windows Task Scheduler integration.

## Connect

```powershell
python -m ntou_pppoe connect
```

Manually establishes the configured PPPoE connection.

After connecting, the application performs a complete network health check and displays diagnostic information.

## Disconnect

```powershell
python -m ntou_pppoe disconnect
```

Disconnects the configured PPPoE profile.

The application waits for and verifies that the PPPoE connection has actually disappeared.

## Status

```powershell
python -m ntou_pppoe status
```

Displays the current connection state, network information, health checks, and retry state.

## Diagnose

```powershell
python -m ntou_pppoe diagnose
```

Displays the currently detected IPv4 address, default gateway, and DNS servers without attempting to establish a new connection.

---

# ⚙️ 設定檔

設定檔位於：

```text
config/config.json
```

範例設定位於：

```text
config/config.example.json
```

## Connection

### `connection_name`

Windows PPPoE connection 的名稱。

```json
"connection_name": "NTOU-PPPoE"
```

必須與 Windows 中的連線名稱一致。

## Service

### `startup_delay`

程式啟動後等待幾秒才開始建立 PPPoE。

```json
"startup_delay": 5
```

### `check_interval`

兩次網路健康檢查之間的間隔秒數。

```json
"check_interval": 30
```

### `connect_timeout`

等待 PPPoE 建立或中斷的最長時間。

```json
"connect_timeout": 30
```

## Health Check

### `enabled`

是否啟用完整網路健康檢查。

```json
"enabled": true
```

### `dns_host`

DNS 測試使用的 hostname。

```json
"dns_host": "example.com"
```

### `https_url`

HTTPS connectivity 測試使用的 URL。

```json
"https_url": "https://www.example.com"
```

### `timeout`

健康檢查使用的 timeout。

```json
"timeout": 5
```

## Retry

### `initial_delay`

第一次 recovery 前等待的時間。

```json
"initial_delay": 5
```

### `max_delay`

Exponential Backoff 的最大等待時間。

```json
"max_delay": 60
```

### `max_attempts`

一個 recovery cycle 中最多嘗試幾次。

```json
"max_attempts": 5
```

例如：

```text
5 秒
 ↓
10 秒
 ↓
20 秒
 ↓
40 秒
 ↓
60 秒
```

等待時間會受到 `max_delay` 限制。

---

# English Configuration

The application configuration is stored in:

```text
config/config.json
```

An example configuration is provided at:

```text
config/config.example.json
```

## Connection

### `connection_name`

The name of the Windows PPPoE connection profile.

```json
"connection_name": "NTOU-PPPoE"
```

It must exactly match the configured Windows connection name.

## Service

### `startup_delay`

Number of seconds to wait before establishing the initial PPPoE connection.

```json
"startup_delay": 5
```

### `check_interval`

Number of seconds between health-check cycles.

```json
"check_interval": 30
```

### `connect_timeout`

Maximum amount of time to wait for a PPPoE connection or disconnection to be verified.

```json
"connect_timeout": 30
```

## Health Check

### `enabled`

Enables or disables network health checks.

```json
"enabled": true
```

### `dns_host`

Hostname used for the DNS resolution test.

```json
"dns_host": "example.com"
```

### `https_url`

URL used for the HTTPS connectivity test.

```json
"https_url": "https://www.example.com"
```

### `timeout`

Timeout used by network health checks.

```json
"timeout": 5
```

## Retry

### `initial_delay`

Initial delay before the first recovery attempt.

```json
"initial_delay": 5
```

### `max_delay`

Maximum delay used by exponential backoff.

```json
"max_delay": 60
```

### `max_attempts`

Maximum number of recovery attempts in a recovery cycle.

```json
"max_attempts": 5
```

For example:

```text
5 seconds
    ↓
10 seconds
    ↓
20 seconds
    ↓
40 seconds
    ↓
60 seconds
```

The delay is capped by `max_delay`.

---

# 🔄 自動重連機制

NTOU PPPoE 不會只依靠單一訊號判斷「有沒有網路」。

程式會先確認：

```text
PPPoE connection
       ↓
IPv4
       ↓
Gateway
       ↓
DNS
       ↓
HTTPS
```

如果健康檢查失敗：

```text
CONNECTED
    ↓
DEGRADED
    ↓
RECOVERING
    ↓
Disconnect
    ↓
Verify disconnected
    ↓
Connect
    ↓
Verify connected
    ↓
CONNECTED
```

如果 recovery attempt 全部失敗，程式會等待並開始新的 recovery cycle，而不是永久鎖死在錯誤狀態。

---

# English Automatic Recovery

NTOU PPPoE does not rely on a single connectivity signal.

The application evaluates several layers:

```text
PPPoE connection
       ↓
IPv4
       ↓
Gateway
       ↓
DNS
       ↓
HTTPS
```

When a health check fails:

```text
CONNECTED
    ↓
DEGRADED
    ↓
RECOVERING
    ↓
Disconnect
    ↓
Verify disconnected
    ↓
Connect
    ↓
Verify connected
    ↓
CONNECTED
```

If all recovery attempts fail, the service resets the recovery window and can begin another recovery cycle later instead of remaining permanently stuck in an error state.

---

# 🩺 網路健康檢查

健康檢查包含五個部分：

| 檢查    | 說明                                        |
| ------- | ------------------------------------------- |
| PPPoE   | Windows RAS 是否仍存在指定 PPPoE connection |
| IPv4    | 是否取得 IPv4 address                       |
| Gateway | 是否存在 default gateway                    |
| DNS     | 是否能解析指定 hostname                     |
| HTTPS   | 是否能建立 HTTPS connection                 |

完整健康狀態必須：

```text
PPPoE   ✓
IPv4    ✓
Gateway ✓
DNS     ✓
HTTPS   ✓
```

才能判定：

```text
Health: 5/5
```

---

# English Network Health Checks

The network health check consists of five independent checks:

| Check   | Description                                                 |
| ------- | ----------------------------------------------------------- |
| PPPoE   | Verifies that the configured RAS PPPoE connection is active |
| IPv4    | Verifies that an IPv4 address is available                  |
| Gateway | Verifies that a default gateway is present                  |
| DNS     | Verifies that the configured hostname can be resolved       |
| HTTPS   | Verifies that an HTTPS request can reach the configured URL |

The connection is considered fully healthy only when all five checks pass:

```text
PPPoE   ✓
IPv4    ✓
Gateway ✓
DNS     ✓
HTTPS   ✓
```

This produces a health score of:

```text
Health: 5/5
```

---

# 📝 日誌

程式會將 log 儲存在：

```text
logs/ntou-pppoe.log
```

例如：

```text
2026-09-30 10:13:58 [INFO] Initializing PPPoE connection.
2026-09-30 10:13:58 [INFO] Connecting to PPPoE profile: NTOU-PPPoE
2026-09-30 10:13:58 [INFO] PPPoE connection established and verified.
2026-09-30 10:13:59 [INFO] Network health check passed. PPPoE=True IPv4=True Gateway=True DNS=True HTTPS=True
```

Log 使用 rotating file handler。

目前設定：

```text
Maximum size: 5 MB
Backup files: 3
```

因此舊 log 不會無限累積。

---

# English Logging

Application logs are stored at:

```text
logs/ntou-pppoe.log
```

Example:

```text
2026-09-30 10:13:58 [INFO] Initializing PPPoE connection.
2026-09-30 10:13:58 [INFO] Connecting to PPPoE profile: NTOU-PPPoE
2026-09-30 10:13:58 [INFO] PPPoE connection established and verified.
2026-09-30 10:13:59 [INFO] Network health check passed. PPPoE=True IPv4=True Gateway=True DNS=True HTTPS=True
```

The logger uses a rotating file handler with:

```text
Maximum size: 5 MB
Backup files: 3
```

This prevents the application log from growing indefinitely.

---

# 🗑️ 解除安裝

如果不再需要自動啟動服務：

```powershell
scripts\uninstall.bat
```

解除安裝會移除：

```text
NTOU-PPPoE Manager
```

Windows Task Scheduler 工作。

但**不會**移除：

```text
config/config.json
logs/
Python
Windows PPPoE connection
```

因此之後重新安裝時，可以保留原本的設定。

---

# English Uninstallation

If you no longer want the application to start automatically:

```powershell
scripts\uninstall.bat
```

The uninstall script removes the:

```text
NTOU-PPPoE Manager
```

scheduled task from Windows Task Scheduler.

It does **not** remove:

```text
config/config.json
logs/
Python
Windows PPPoE connection
```

This allows the existing configuration to remain available if the application is installed again later.

---

# ❓ 常見問題

## 為什麼程式無法連線？

先確認 Windows 本身可以手動連線 PPPoE。

接著確認：

```json
"connection_name": "你的 PPPoE 連線名稱"
```

與 Windows 中的名稱完全一致。

可以先執行：

```powershell
python -m ntou_pppoe connect
```

查看實際錯誤訊息。

## 為什麼 `status` 顯示 PPPoE 正常，但 Health 不是 5/5？

代表 PPPoE connection 仍存在，但其他網路層級可能發生問題。

例如：

```text
PPPoE   ✓
IPv4    ✓
Gateway ✓
DNS     ✗
HTTPS   ✗
```

這表示 PPPoE session 還在，但 DNS 或 Internet connectivity 可能有問題。

可以執行：

```powershell
python -m ntou_pppoe diagnose
```

查看 IPv4、Gateway 與 DNS。

## 為什麼沒有看到 CMD 視窗？

這是正常的。

Task Scheduler 會透過：

```text
pythonw.exe
```

在背景執行服務。

如果需要查看服務狀況，可以查看：

```text
logs/ntou-pppoe.log
```

或手動執行：

```powershell
python -m ntou_pppoe status
```

## 為什麼 `python -m ntou_pppoe` 可以執行，但 `ntou-pppoe` 不行？

通常代表 Python Scripts 目錄沒有加入 PATH。

可以直接使用：

```powershell
python -m ntou_pppoe
```

## 可以把 `config/config.json` 上傳到 GitHub 嗎？

不建議。

`config/config.json` 已經被 `.gitignore` 排除。

repository 只應該保留：

```text
config/config.example.json
```

請不要將 PPPoE 帳號、密碼或其他私人資訊提交到公開 repository。

---

# English Troubleshooting

## Why can't the application connect?

First verify that the PPPoE connection works manually through Windows.

Then verify that:

```json
"connection_name": "Your PPPoE Connection Name"
```

exactly matches the Windows PPPoE profile name.

You can run:

```powershell
python -m ntou_pppoe connect
```

to see the connection result and any reported error.

## Why does `status` show PPPoE as connected but Health is not 5/5?

This means that the PPPoE session still exists, but another layer of network connectivity may be failing.

For example:

```text
PPPoE   ✓
IPv4    ✓
Gateway ✓
DNS     ✗
HTTPS   ✗
```

The PPPoE session is still active, but DNS resolution or Internet connectivity may not be working.

Run:

```powershell
python -m ntou_pppoe diagnose
```

to inspect the detected IPv4 address, gateway, and DNS servers.

## Why don't I see a CMD window?

This is expected when the application is started through Task Scheduler.

The scheduled task launches:

```text
pythonw.exe
```

so the service can run in the background without opening a Python console.

Check:

```text
logs/ntou-pppoe.log
```

for service activity, or run:

```powershell
python -m ntou_pppoe status
```

manually.

## Why does `python -m ntou_pppoe` work but `ntou-pppoe` does not?

The Python Scripts directory may not be included in your PATH.

You can always use:

```powershell
python -m ntou_pppoe
```

directly.

## Can I upload `config/config.json` to GitHub?

You should not.

`config/config.json` is excluded by `.gitignore`.

The repository should only contain:

```text
config/config.example.json
```

Do not commit PPPoE credentials or other private information to a public repository.

---

# 🧪 開發與測試

安裝開發依賴：

```powershell
python -m pip install -r requirements.txt
```

執行完整測試：

```powershell
python -m pytest
```

目前測試涵蓋：

- Configuration
- Configuration validation
- Connectivity
- Network diagnostics
- PPPoE / RAS
- RAS connection enumeration
- Retry controller
- Connection state
- Service behavior
- Connection manager
- CLI
- Terminal dashboard

目前專案中的 Windows PPPoE / RAS 功能需要在 Windows 環境下進行實際驗證。

---

# English Development and Testing

Install the project dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run the complete test suite:

```powershell
python -m pytest
```

The test suite covers:

- Configuration loading
- Configuration validation
- Connectivity checks
- Network diagnostics
- PPPoE / Windows RAS handling
- RAS connection enumeration
- Retry controller
- Connection state management
- Service behavior
- Connection manager
- CLI behavior
- Terminal dashboard

The Windows PPPoE and RAS functionality requires Windows for full integration testing.

---

# 📁 專案結構

```text
ntou-pppoe/
├── config/
│   ├── config.example.json
│   └── config.json
│
├── logs/
│   └── .gitkeep
│
├── scripts/
│   ├── install.bat
│   ├── start.bat
│   └── uninstall.bat
│
├── src/
│   └── ntou_pppoe/
│       ├── config/
│       │   ├── loader.py
│       │   └── validator.py
│       │
│       ├── core/
│       │   ├── manager.py
│       │   ├── retry.py
│       │   ├── service.py
│       │   └── state.py
│       │
│       ├── network/
│       │   ├── connectivity.py
│       │   ├── diagnostics.py
│       │   └── pppoe.py
│       │
│       ├── ui/
│       │   └── dashboard.py
│       │
│       ├── utils/
│       │   ├── logger.py
│       │   └── system.py
│       │
│       ├── __init__.py
│       ├── __main__.py
│       └── cli.py
│
├── tests/
│
├── .gitignore
├── LICENSE
├── pyproject.toml
├── README.md
└── requirements.txt
```

---

# English Project Structure

```text
ntou-pppoe/
├── config/
│   ├── config.example.json
│   └── config.json
│
├── logs/
│   └── .gitkeep
│
├── scripts/
│   ├── install.bat
│   ├── start.bat
│   └── uninstall.bat
│
├── src/
│   └── ntou_pppoe/
│       ├── config/
│       │   ├── loader.py
│       │   └── validator.py
│       │
│       ├── core/
│       │   ├── manager.py
│       │   ├── retry.py
│       │   ├── service.py
│       │   └── state.py
│       │
│       ├── network/
│       │   ├── connectivity.py
│       │   ├── diagnostics.py
│       │   └── pppoe.py
│       │
│       ├── ui/
│       │   └── dashboard.py
│       │
│       ├── utils/
│       │   ├── logger.py
│       │   └── system.py
│       │
│       ├── __init__.py
│       ├── __main__.py
│       └── cli.py
│
├── tests/
│
├── .gitignore
├── LICENSE
├── README.md
├── pyproject.toml
└── requirements.txt
```

---

# 🔐 安全性

本專案不需要將 PPPoE 密碼寫入 Python 程式或 Git repository。

Windows 會負責管理 PPPoE connection 的登入資訊，而本程式透過 Windows RAS API 使用已設定的 connection profile。

請注意：

- 不要提交 `config/config.json`
- 不要提交可能包含私人網路資訊的 log
- 不要在 GitHub issue 或 discussion 中公開帳號密碼
- 不要將自己的 PPPoE 設定檔直接分享給其他人

`.gitignore` 已經預設排除：

```text
config/config.json
logs/*.log
__pycache__/
.pytest_cache/
*.egg-info/
```

---

# English Security

This project does not require PPPoE passwords to be stored in the Python source code or Git repository.

Windows manages the credentials associated with the PPPoE connection profile, while the application uses the Windows RAS API to access the configured connection.

Please follow these guidelines:

- Do not commit `config/config.json`
- Do not commit logs containing private network information
- Do not post PPPoE credentials in GitHub issues or discussions
- Do not share your personal PPPoE configuration file with others

The repository `.gitignore` excludes:

```text
config/config.json
logs/*.log
__pycache__/
.pytest_cache/
*.egg-info/
```

---

# 🤝 給海大同學

如果你只是想讓宿舍網路自動連線，通常不需要理解這個專案的內部實作。

大致流程：

```text
建立 Windows PPPoE
        ↓
下載 NTOU PPPoE
        ↓
設定 connection_name
        ↓
執行 install.bat
        ↓
登入 Windows
        ↓
自動連線
        ↓
斷線時自動重新連線
```

如果遇到問題，可以先執行：

```powershell
python -m ntou_pppoe status
```

以及：

```powershell
python -m ntou_pppoe diagnose
```

再查看：

```text
logs/ntou-pppoe.log
```

如果仍然無法解決，再帶著錯誤訊息與相關 log 回報問題。

---

# English Quick Start for NTOU Students

If you only want the dormitory PPPoE connection to work automatically, you do not need to understand the internal implementation.

The basic workflow is:

```text
Create a Windows PPPoE connection
        ↓
Download NTOU PPPoE
        ↓
Set connection_name
        ↓
Run install.bat
        ↓
Log into Windows
        ↓
Automatic connection
        ↓
Automatic reconnection after failures
```

If you encounter a problem, start with:

```powershell
python -m ntou_pppoe status
```

and:

```powershell
python -m ntou_pppoe diagnose
```

Then inspect:

```text
logs/ntou-pppoe.log
```

When reporting an issue, include the relevant error message and log information while removing any private information first.

---

# 📄 License

This project is licensed under the MIT License.

See [LICENSE](LICENSE) for the full license text.
