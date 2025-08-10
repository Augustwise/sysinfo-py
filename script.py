import os
import platform
import ctypes
import subprocess
import glob
import re
import datetime as _dt

def get_logical_cpu_count() -> int:
    count = os.cpu_count()
    return count if isinstance(count, int) and count > 0 else 1

def _get_physical_cpu_count_with_psutil() -> int | None:
    try:
        import psutil
        value = psutil.cpu_count(logical=False)
        if isinstance(value, int) and value > 0:
            return value
        return None
    except Exception:
        return None

def _get_physical_cpu_count_windows() -> int | None:
    try:
        cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            "[int](Get-CimInstance Win32_Processor | Measure-Object -Property NumberOfCores -Sum).Sum",
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0:
            text_value = result.stdout.strip()
            value = int(text_value)
            if value > 0:
                return value
    except Exception:
        return None
    return None

def _get_physical_cpu_count_linux() -> int | None:
    try:
        pairs: set[tuple[str, str]] = set()
        physical_id: str | None = None
        core_id: str | None = None
        with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    if physical_id is not None and core_id is not None:
                        pairs.add((physical_id, core_id))
                    physical_id, core_id = None, None
                    continue
                if line.startswith("physical id"):
                    physical_id = line.split(":", 1)[1].strip()
                elif line.startswith("core id"):
                    core_id = line.split(":", 1)[1].strip()
            if physical_id is not None and core_id is not None:
                pairs.add((physical_id, core_id))
        if pairs:
            return len(pairs)
    except Exception:
        pass
    try:
        pairs_sys: set[tuple[str, str]] = set()
        for core_path in glob.glob("/sys/devices/system/cpu/cpu[0-9]*/topology/core_id"):
            cpu_topology_dir = os.path.dirname(core_path)
            with open(core_path, "r", encoding="utf-8") as f_core:
                core_val = f_core.read().strip()
            pkg_path = os.path.join(cpu_topology_dir, "physical_package_id")
            if os.path.exists(pkg_path):
                with open(pkg_path, "r", encoding="utf-8") as f_pkg:
                    pkg_val = f_pkg.read().strip()
            else:
                pkg_val = "0"
            pairs_sys.add((pkg_val, core_val))
        if pairs_sys:
            return len(pairs_sys)
    except Exception:
        pass
    try:
        with open("/proc/cpuinfo", "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if line.lower().startswith("cpu cores"):
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        value = int(parts[1].strip())
                        if value > 0:
                            return value
                    break
    except Exception:
        pass
    return None

def get_physical_cpu_count() -> int:
    value = _get_physical_cpu_count_with_psutil()
    if isinstance(value, int) and value > 0:
        return value
    system = platform.system()
    if system == "Windows":
        value = _get_physical_cpu_count_windows()
    elif system == "Linux":
        value = _get_physical_cpu_count_linux()
    else:
        value = None
    if isinstance(value, int) and value > 0:
        return value
    return get_logical_cpu_count()

def _get_windows_build_number() -> str | None:
    try:
        import winreg
        reg_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
        access = winreg.KEY_READ
        if hasattr(winreg, "KEY_WOW64_64KEY"):
            access |= winreg.KEY_WOW64_64KEY
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, access) as key:
            current_build, _ = winreg.QueryValueEx(key, "CurrentBuild")
            try:
                ubr, _ = winreg.QueryValueEx(key, "UBR")
                return f"{current_build}.{ubr}"
            except FileNotFoundError:
                return str(current_build)
    except Exception:
        return None

def get_os_name() -> str:
    system = platform.system()
    if system == "Windows":
        try:
            edition = getattr(platform, "win32_edition", lambda: "")()
        except Exception:
            edition = ""
        release = platform.release()
        build_number = _get_windows_build_number()
        if build_number:
            version = build_number
        else:
            version = platform.version()
        edition_str = f" {edition}" if edition else ""
        return f"Windows {release}{edition_str} (build {version})"
    if system == "Linux":
        try:
            pretty: str | None = None
            with open("/etc/os-release", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        pretty = line.split("=", 1)[1].strip().strip('"')
                        break
            if pretty:
                return pretty
        except Exception:
            pass
        return platform.platform()
    return platform.platform()

def _get_windows_install_datetime() -> _dt.datetime | None:
    try:
        import winreg
        reg_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
        access = winreg.KEY_READ
        if hasattr(winreg, "KEY_WOW64_64KEY"):
            access |= winreg.KEY_WOW64_64KEY
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path, 0, access) as key:
            value, _ = winreg.QueryValueEx(key, "InstallDate")
        seconds = int(value)
        return _dt.datetime.fromtimestamp(seconds, tz=_dt.timezone.utc).astimezone()
    except Exception:
        return None

def _get_linux_install_datetime() -> _dt.datetime | None:
    candidate_paths = [
        "/var/log/installer/syslog",
        "/var/log/anaconda/anaconda.log",
        "/var/log/installer",
        "/etc",
    ]
    timestamps: list[_dt.datetime] = []
    for path in candidate_paths:
        try:
            stat = os.stat(path)
            ts = _dt.datetime.fromtimestamp(stat.st_mtime, tz=_dt.timezone.utc).astimezone()
            timestamps.append(ts)
        except Exception:
            continue
    if timestamps:
        return min(timestamps)
    return None

def get_os_install_datetime() -> _dt.datetime | None:
    system = platform.system()
    if system == "Windows":
        return _get_windows_install_datetime()
    if system == "Linux":
        return _get_linux_install_datetime()
    return None

def format_datetime_local(dt: _dt.datetime) -> str:
    return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")

def _get_total_ram_bytes_windows() -> int:
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]
    mem_status = MEMORYSTATUSEX()
    mem_status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    result = ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem_status))
    if not result:
        raise OSError("GlobalMemoryStatusEx failed")
    return int(mem_status.ullTotalPhys)

def _get_total_ram_bytes_linux() -> int:
    meminfo_path = "/proc/meminfo"
    try:
        with open(meminfo_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    parts = line.split()
                    if len(parts) >= 3:
                        value = int(parts[1])
                        unit = parts[2].lower()
                        if unit == "kb":
                            return value * 1024
                        if unit == "mb":
                            return value * 1024 * 1024
                        if unit == "gb":
                            return value * 1024 * 1024 * 1024
                        return value * 1024
                    break
    except FileNotFoundError:
        pass
    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        phys_pages = os.sysconf("SC_PHYS_PAGES")
        return int(page_size) * int(phys_pages)
    except (ValueError, OSError, AttributeError) as exc:
        raise RuntimeError("Unable to determine total RAM on Linux") from exc

def _get_free_ram_bytes_windows() -> int:
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]
    mem_status = MEMORYSTATUSEX()
    mem_status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    result = ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem_status))
    if not result:
        raise OSError("GlobalMemoryStatusEx failed")
    return int(mem_status.ullAvailPhys)

def _get_free_ram_bytes_linux() -> int:
    meminfo_path = "/proc/meminfo"
    try:
        available_value: int | None = None
        free_value: int | None = None
        with open(meminfo_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    parts = line.split()
                    if len(parts) >= 3:
                        value = int(parts[1])
                        unit = parts[2].lower()
                        if unit == "kb":
                            available_value = value * 1024
                        elif unit == "mb":
                            available_value = value * 1024 * 1024
                        elif unit == "gb":
                            available_value = value * 1024 * 1024 * 1024
                        else:
                            available_value = value * 1024
                        break
                elif line.startswith("MemFree:"):
                    parts = line.split()
                    if len(parts) >= 3:
                        value = int(parts[1])
                        unit = parts[2].lower()
                        if unit == "kb":
                            free_value = value * 1024
                        elif unit == "mb":
                            free_value = value * 1024 * 1024
                        elif unit == "gb":
                            free_value = value * 1024 * 1024 * 1024
                        else:
                            free_value = value * 1024
        if available_value is not None:
            return available_value
        if free_value is not None:
            return free_value
    except FileNotFoundError:
        pass
    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        avail_pages = os.sysconf("SC_AVPHYS_PAGES")
        return int(page_size) * int(avail_pages)
    except (ValueError, OSError, AttributeError) as exc:
        raise RuntimeError("Unable to determine free RAM on Linux") from exc

def get_total_ram_bytes() -> int:
    system = platform.system()
    if system == "Windows":
        return _get_total_ram_bytes_windows()
    if system == "Linux":
        return _get_total_ram_bytes_linux()
    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        phys_pages = os.sysconf("SC_PHYS_PAGES")
        return int(page_size) * int(phys_pages)
    except Exception as exc:
        raise NotImplementedError(f"Unsupported OS: {system}") from exc

def get_free_ram_bytes() -> int:
    system = platform.system()
    if system == "Windows":
        return _get_free_ram_bytes_windows()
    if system == "Linux":
        return _get_free_ram_bytes_linux()
    try:
        page_size = os.sysconf("SC_PAGE_SIZE")
        avail_pages = os.sysconf("SC_AVPHYS_PAGES")
        return int(page_size) * int(avail_pages)
    except Exception as exc:
        raise NotImplementedError(f"Unsupported OS: {system}") from exc

def format_bytes_as_gb(num_bytes: int) -> str:
    gib = num_bytes / (1024 ** 3)
    return f"{gib:.2f} GB"

def format_bytes_as_mb(num_bytes: int) -> str:
    mib = num_bytes / (1024 ** 2)
    return f"{mib:.2f} MB"

def _unique_ordered(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        value = item.strip()
        if not value:
            continue
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result

def _get_gpu_names_windows() -> list[str]:
    names: list[str] = []
    try:
        cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name",
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=5, check=False
        )
        if result.returncode == 0 and result.stdout:
            for line in result.stdout.splitlines():
                value = line.strip()
                if value:
                    names.append(value)
    except Exception:
        pass
    if not names:
        try:
            cmd = [
                "wmic",
                "path",
                "Win32_VideoController",
                "get",
                "Name",
                "/value",
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=5, check=False
            )
            if result.returncode == 0 and result.stdout:
                for line in result.stdout.splitlines():
                    if line.startswith("Name="):
                        value = line.split("=", 1)[1].strip()
                        if value:
                            names.append(value)
        except Exception:
            pass
    return _unique_ordered(names)

def _get_gpu_names_linux() -> list[str]:
    names: list[str] = []
    try:
        result = subprocess.run(
            ["lspci", "-mm", "-nn"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0 and result.stdout:
            for raw_line in result.stdout.splitlines():
                line = raw_line.strip()
                if not line:
                    continue
                if (
                    '"VGA compatible controller"' in line
                    or '"3D controller"' in line
                    or '"Display controller"' in line
                ):
                    fields = re.findall(r'"([^"]+)"', line)
                    if len(fields) >= 3:
                        vendor = fields[1]
                        device = fields[2]
                        names.append(f"{vendor} {device}")
    except Exception:
        pass
    if not names:
        try:
            for info_path in glob.glob("/proc/driver/nvidia/gpus/*/information"):
                try:
                    with open(info_path, "r", encoding="utf-8") as f:
                        for rline in f:
                            if rline.startswith("Model:"):
                                value = rline.split(":", 1)[1].strip()
                                if value:
                                    names.append(f"NVIDIA {value}")
                                break
                except Exception:
                    continue
        except Exception:
            pass
    if not names:
        try:
            vendor_map = {
                "0x10de": "NVIDIA",
                "10de": "NVIDIA",
                "0x1002": "AMD/ATI",
                "1002": "AMD/ATI",
                "0x8086": "Intel",
                "8086": "Intel",
                "0x1a03": "ASPEED",
                "1a03": "ASPEED",
            }
            for card_path in glob.glob("/sys/class/drm/card[0-9]*"):
                uevent = os.path.join(card_path, "device", "uevent")
                if not os.path.exists(uevent):
                    continue
                try:
                    with open(uevent, "r", encoding="utf-8") as f:
                        driver: str | None = None
                        pci_id: str | None = None
                        for rline in f:
                            if rline.startswith("DRIVER="):
                                driver = rline.split("=", 1)[1].strip()
                            elif rline.startswith("PCI_ID="):
                                pci_id = rline.split("=", 1)[1].strip()
                        if pci_id:
                            vendor_hex = pci_id.split(":")[0]
                            vendor_name = vendor_map.get(vendor_hex.lower())
                            if vendor_name:
                                if driver:
                                    names.append(f"{vendor_name} ({driver})")
                                else:
                                    names.append(f"{vendor_name} GPU")
                except Exception:
                    continue
        except Exception:
            pass
    return _unique_ordered(names)

def get_gpu_names() -> list[str]:
    system = platform.system()
    if system == "Windows":
        return _get_gpu_names_windows()
    if system == "Linux":
        return _get_gpu_names_linux()
    return []

def table_lines(
    rows: list[tuple[str, str]], header: tuple[str, str] | None = ("Property", "Value")
) -> list[str]:
    col1_width = max([len(header[0]) if header else 0] + [len(k) for k, _ in rows])
    col2_width = max([len(header[1]) if header else 0] + [len(v) for _, v in rows])
    def sep(char: str) -> str:
        return f"+-{char * col1_width}-+-{char * col2_width}-+"
    lines: list[str] = []
    lines.append(sep("-"))
    if header is not None:
        lines.append(
            f"| {header[0].ljust(col1_width)} | {header[1].ljust(col2_width)} |"
        )
        lines.append(sep("="))
    for key, value in rows:
        lines.append(f"| {key.ljust(col1_width)} | {value.ljust(col2_width)} |")
    lines.append(sep("-"))
    return lines

def main() -> None:
    os_name = get_os_name()
    install_dt = get_os_install_datetime()
    physical_cores = get_physical_cpu_count()
    logical_cores = get_logical_cpu_count()
    total_ram_bytes = get_total_ram_bytes()
    free_ram_bytes = get_free_ram_bytes()
    gpu_names = get_gpu_names()
    gpu_display = ", ".join(gpu_names) if gpu_names else "Unknown"
    install_display = (
        format_datetime_local(install_dt) if install_dt is not None else "Unknown"
    )
    rows: list[tuple[str, str]] = [
        ("Operating system", os_name),
        ("OS install date", install_display),
        ("Physical cores", str(physical_cores)),
        ("Logical cores", str(logical_cores)),
        ("GPU(s)", gpu_display),
        ("Total RAM", format_bytes_as_gb(total_ram_bytes)),
        ("Free RAM", format_bytes_as_mb(free_ram_bytes)),
    ]
    for line in table_lines(rows):
        print(line)

main()
