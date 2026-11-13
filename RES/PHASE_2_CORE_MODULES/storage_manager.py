from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from RES.PHASE_4_TESTING.error_handling import PathValidationError
from RES.PHASE_4_TESTING.validation import InputValidator


class StorageManager:
    def __init__(self, jobs_dir: Path, demo_dir: Path, reports_dir: Path, logs_dir: Path):
        self.jobs_dir = Path(jobs_dir)
        self.demo_dir = Path(demo_dir)
        self.reports_dir = Path(reports_dir)
        self.logs_dir = Path(logs_dir)
        for directory in [self.jobs_dir, self.demo_dir, self.reports_dir, self.logs_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def get_directory_map(self) -> Dict[str, Path]:
        return {
            "jobs": self.jobs_dir,
            "demo": self.demo_dir,
            "reports": self.reports_dir,
            "logs": self.logs_dir,
        }

    def list_files(self, area: str = "jobs") -> List[Dict[str, Any]]:
        directories = self.get_directory_map()
        target_dir = directories.get(area, self.jobs_dir)
        items: List[Dict[str, Any]] = []
        for path in sorted(target_dir.rglob("*")):
            if path.is_file() and path.name != ".gitkeep":
                stat = path.stat()
                items.append(
                    {
                        "name": path.name,
                        "relative_path": str(path.relative_to(target_dir)),
                        "full_path": str(path),
                        "size_bytes": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )
        return items

    def get_storage_summary(self) -> Dict[str, Dict[str, Any]]:
        summary: Dict[str, Dict[str, Any]] = {}
        for label, directory in self.get_directory_map().items():
            files = [p for p in directory.rglob("*") if p.is_file() and p.name != ".gitkeep"]
            total_bytes = sum(p.stat().st_size for p in files)
            summary[label] = {
                "path": str(directory),
                "file_count": len(files),
                "total_bytes": total_bytes,
                "total_kb": round(total_bytes / 1024, 2),
            }
        return summary

    def inspect_file(self, raw_path: str, max_lines: int = 40) -> str:
        resolved = InputValidator.validate_safe_path(
            raw_path,
            allowed_roots=[self.jobs_dir, self.demo_dir, self.reports_dir, self.logs_dir],
            must_exist=True,
        )
        if not resolved.is_file():
            raise PathValidationError(f"'{resolved}' is not a regular file.")
        lines = resolved.read_text(encoding="utf-8", errors="replace").splitlines()
        return "\n".join(lines[:max_lines])

    def delete_temp_file(self, raw_path: str) -> str:
        resolved = InputValidator.validate_safe_path(
            raw_path,
            allowed_roots=[self.jobs_dir, self.reports_dir],
            must_exist=True,
        )
        if resolved.name == ".gitkeep" or not resolved.is_file():
            raise PathValidationError("Only regular application-generated files in jobs/ or reports/ may be deleted.")
        resolved.unlink()
        return str(resolved)

