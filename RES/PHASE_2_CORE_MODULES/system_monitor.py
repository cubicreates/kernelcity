import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import psutil

from RES.PHASE_4_TESTING.error_handling import ProcessExecutionError


class SystemMonitor:
    PROTECTED_NAMES: Set[str] = {
        "system", "system idle process", "registry", "smss.exe", "csrss.exe",
        "wininit.exe", "services.exe", "lsass.exe", "svchost.exe", "init",
        "systemd", "kthreadd", "launchd",
    }

    def __init__(self, base_dir: Path, cpu_threshold: float = 80.0, ram_threshold: float = 80.0, disk_threshold: float = 85.0):
        self.base_dir = Path(base_dir)
        self.cpu_threshold = cpu_threshold
        self.ram_threshold = ram_threshold
        self.disk_threshold = disk_threshold

    def update_thresholds(self, cpu_threshold: float, ram_threshold: float, disk_threshold: float) -> None:
        self.cpu_threshold = cpu_threshold
        self.ram_threshold = ram_threshold
        self.disk_threshold = disk_threshold

    def get_system_snapshot(self) -> Dict[str, Any]:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count_logical = psutil.cpu_count(logical=True) or 1
        cpu_count_physical = psutil.cpu_count(logical=False) or cpu_count_logical
        vm = psutil.virtual_memory()
        disk = psutil.disk_usage(str(self.base_dir))
        process_count = len(psutil.pids())

        warnings: List[str] = []
        if cpu_percent >= self.cpu_threshold:
            warnings.append(f"CPU usage {cpu_percent:.1f}% exceeds threshold {self.cpu_threshold:.1f}%")
        if vm.percent >= self.ram_threshold:
            warnings.append(f"RAM usage {vm.percent:.1f}% exceeds threshold {self.ram_threshold:.1f}%")
        if disk.percent >= self.disk_threshold:
            warnings.append(f"Disk usage {disk.percent:.1f}% exceeds threshold {self.disk_threshold:.1f}%")

        return {
            "source": "LIVE",
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "cpu_percent": round(cpu_percent, 1),
            "cpu_count_logical": cpu_count_logical,
            "cpu_count_physical": cpu_count_physical,
            "ram_percent": round(vm.percent, 1),
            "ram_total_gb": round(vm.total / (1024 ** 3), 2),
            "ram_available_gb": round(vm.available / (1024 ** 3), 2),
            "ram_used_gb": round(vm.used / (1024 ** 3), 2),
            "disk_percent": round(disk.percent, 1),
            "disk_total_gb": round(disk.total / (1024 ** 3), 2),
            "disk_free_gb": round(disk.free / (1024 ** 3), 2),
            "active_processes": process_count,
            "status": "WARNING" if warnings else "OPERATIONAL",
            "warnings": warnings,
        }

    def list_host_processes(
        self,
        kernel_pids: Optional[Set[int]] = None,
        name_filter: str = "",
        limit: int = 30,
    ) -> List[Dict[str, Any]]:
        tracked = kernel_pids or set()
        query = (name_filter or "").strip().lower()
        results: List[Dict[str, Any]] = []

        for proc in psutil.process_iter(["pid", "name", "status", "cpu_percent", "memory_info", "create_time"]):
            try:
                info = proc.info
                pid = info.get("pid")
                name = info.get("name") or "unknown"
                if query and query not in name.lower() and query != str(pid):
                    continue
                mem_info = info.get("memory_info")
                mem_mb = round(mem_info.rss / (1024 ** 2), 2) if mem_info else 0.0
                ctime = info.get("create_time")
                created = datetime.fromtimestamp(ctime).strftime("%Y-%m-%d %H:%M:%S") if ctime else "N/A"
                results.append(
                    {
                        "pid": pid,
                        "name": name,
                        "status": info.get("status") or "unknown",
                        "cpu_percent": round(info.get("cpu_percent") or 0.0, 1),
                        "memory_mb": mem_mb,
                        "created": created,
                        "kernel_city_owned": pid in tracked,
                    }
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        results.sort(key=lambda item: (not item["kernel_city_owned"], -item["memory_mb"]))
        return results[:limit]

    def inspect_process(self, pid: int, kernel_pids: Optional[Set[int]] = None) -> Dict[str, Any]:
        tracked = kernel_pids or set()
        try:
            proc = psutil.Process(pid)
            with proc.oneshot():
                mem = proc.memory_info()
                return {
                    "source": "LIVE",
                    "pid": pid,
                    "name": proc.name(),
                    "status": proc.status(),
                    "cpu_percent": round(proc.cpu_percent(interval=0.05), 1),
                    "memory_mb": round(mem.rss / (1024 ** 2), 2),
                    "num_threads": proc.num_threads(),
                    "created": datetime.fromtimestamp(proc.create_time()).strftime("%Y-%m-%d %H:%M:%S"),
                    "kernel_city_owned": pid in tracked,
                    "protected": self.is_protected_process(pid, proc.name()),
                }
        except psutil.NoSuchProcess as exc:
            raise ProcessExecutionError(f"Process {pid} no longer exists.") from exc
        except psutil.AccessDenied as exc:
            raise ProcessExecutionError(f"Access denied when inspecting process {pid}.") from exc

    def is_protected_process(self, pid: int, name: str = "") -> bool:
        if pid <= 4 or pid == os.getpid():
            return True
        if name.strip().lower() in self.PROTECTED_NAMES:
            return True
        return False

    def terminate_host_process(self, pid: int, kernel_pids: Optional[Set[int]] = None) -> str:
        info = self.inspect_process(pid, kernel_pids=kernel_pids)
        if info["protected"]:
            raise ProcessExecutionError(f"Refusing to terminate protected system/application process PID {pid} ({info['name']}).")
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            proc.wait(timeout=3)
            return f"Process PID {pid} ({info['name']}) terminated."
        except psutil.TimeoutExpired:
            proc.kill()
            return f"Process PID {pid} ({info['name']}) forcefully killed."
        except (psutil.NoSuchProcess, psutil.AccessDenied) as exc:
            raise ProcessExecutionError(f"Unable to terminate PID {pid}: {exc}") from exc

