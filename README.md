# System Information Script
A lightweight Python script that gathers and displays comprehensive system information in a tabular format. This cross-platform tool provides essential hardware and software details about your computer without requiring external dependencies.

## Features

- **Operating System Information**: OS name, version, build number, and installation date
- **CPU Details**: Both physical and logical core counts
- **Memory Information**: Total and available RAM
- **GPU Detection**: Identifies graphics cards across different vendors
- **Cross-Platform Support**: Works on Windows and Linux

## Requirements

- Python 3.8 or higher
- `psutil` library for enhanced CPU detection accuracy

## Installation

1. Clone this repo:

```bash
git clone https://github.com/augustwise/sysinfo-py.git
cd sysinfo-py
```

2. Install `psutil` for better CPU core detection:

```bash
pip install psutil
```

## Usage

Run the script directly:

```bash
python script.py
```

### Sample Output

```
+------------------+---------------------------------------------+
| Property         | Value                                       |
+-================-+-===========================================-+
| Operating system | Windows 11 Professional (build 26100.4652)  |
| OS install date  | 2025-04-30 12:51:27 FLE Daylight Time       |
| Physical cores   | 4                                           |
| Logical cores    | 8                                           |
| GPU(s)           | AMD RadeonT RX 640, AMD Radeon(TM) Graphics |
| Total RAM        | 15.35 GB                                    |
| Free RAM         | 8504.98 MB                                  |
+------------------+---------------------------------------------+
```

## Platform Support

### Windows

- [x] OS version and build detection via Windows Registry
- [x] Install date from Registry
- [x] CPU core count via PowerShell and WMI
- [x] Memory information via Windows API
- [x] GPU detection via PowerShell and WMIC

### Linux

- [x] OS information from `/etc/os-release`
- [x] Install date estimation from system directories
- [x] CPU core count from `/proc/cpuinfo` and `sysfs`
- [x] Memory information from `/proc/meminfo`
- [x] GPU detection via lspci, NVIDIA drivers, and DRM subsystem

## Screenshots:
<img width="600" height="350" alt="image" src="https://github.com/user-attachments/assets/0215b825-f503-4efe-ad11-3dcb4fb75e3d" />

<img width="600" height="350" alt="image" src="https://github.com/user-attachments/assets/1d023d73-2d7a-4520-b664-c6c6cbb2f4a4" />

<img width="600" height="350" alt="image" src="https://github.com/user-attachments/assets/23ab0ff8-2ae9-4cdd-8f77-a4562dc109ba" />


