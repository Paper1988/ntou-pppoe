# NTOU PPPoE

A lightweight Windows utility for automatically connecting
and reconnecting to PPPoE networks.

> Designed for personal use with NTOU dormitory network.

## Features

- Automatic PPPoE connection
- Automatic reconnection
- Configurable retry interval
- Configurable startup delay
- Windows startup integration
- No third-party dependencies

## Requirements

- Windows 10 / 11
- Python 3.10+
- A configured PPPoE connection

## Installation

Clone the repository:

```bash
git clone https://github.com/your-name/ntou-pppoe.git
cd ntou-pppoe
```

Copy the example configuration:

```bash
config/config.example.json
→
config/config.json
```

Edit your PPPoE credentials in `config.json`.

Then run:

```bash
scripts/install.bat
```
