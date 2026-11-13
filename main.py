import runpy
import sys
from pathlib import Path

from GUI.city import KernelCityGUI
from RES.kernel import KernelEngine


def _run_worker_mode() -> int:
    mode = sys.argv[2]
    if mode == "exec_code" and len(sys.argv) >= 4:
        code = sys.argv[3]
        sys.argv = ["worker"] + sys.argv[4:]
        exec(compile(code, "<kernel_city_worker>", "exec"), {"__name__": "__main__"})
        return 0
    if mode == "exec_script" and len(sys.argv) >= 4:
        script_path = sys.argv[3]
        sys.argv = [script_path] + sys.argv[4:]
        runpy.run_path(script_path, run_name="__main__")
        return 0
    return 1


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    if len(sys.argv) >= 3 and sys.argv[1] == "--kc-worker":
        return _run_worker_mode()

    if getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).resolve().parent
    else:
        base_dir = Path(__file__).resolve().parent

    kernel = KernelEngine(base_dir=base_dir)
    exit_code = 0
    try:
        interface = KernelCityGUI(kernel)
        interface.run()
    except KeyboardInterrupt:
        exit_code = 0
    except Exception as exc:
        kernel.logger.log_event("SYSTEM", f"Fatal unhandled error: {exc}", level="ERROR")
        print(f"Kernel City encountered a fatal error: {exc}", file=sys.stderr)
        exit_code = 1
    finally:
        kernel.shutdown()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
