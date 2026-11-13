from typing import TYPE_CHECKING, Any, Dict

from RES.PHASE_5_DEMONSTRATION.demo_datasets import (
    ensure_demo_input_files,
    get_demo_banker_scenario,
    get_demo_deadlock_scenario,
    get_demo_memory_scenario,
    get_demo_scheduling_jobs,
)

if TYPE_CHECKING:
    from RES.kernel import KernelEngine


class DemoEngine:
    def __init__(self, kernel: "KernelEngine"):
        self.kernel = kernel

    def run_scheduling_demo(self, quantum: int = 2) -> Dict[str, Any]:
        jobs = get_demo_scheduling_jobs()
        comparison = self.kernel.analytics.run_scheduling_analysis(self.kernel.scheduler, jobs, quantum=quantum)
        chart_path = self.kernel.analytics.charts.generate_scheduling_comparison_chart(
            comparison["reports"],
            filename="demo_scheduling_comparison.png",
        )
        return {
            "mode": "DEMO",
            "jobs": jobs,
            "quantum": quantum,
            "comparison": comparison,
            "chart_path": str(chart_path),
        }

    def run_memory_demo(self) -> Dict[str, Any]:
        scenario = get_demo_memory_scenario()
        comparison = self.kernel.analytics.run_memory_analysis(
            self.kernel.memory_manager,
            scenario["block_sizes"],
            scenario["requests"],
        )
        chart_path = self.kernel.analytics.charts.generate_memory_comparison_chart(
            comparison["results"],
            filename="demo_memory_comparison.png",
        )
        return {
            "mode": "DEMO",
            "block_sizes": scenario["block_sizes"],
            "requests": scenario["requests"],
            "comparison": comparison,
            "chart_path": str(chart_path),
        }

    def run_banker_demo(self) -> Dict[str, Any]:
        scenario = get_demo_banker_scenario()
        self.kernel.resource_manager.configure_state(
            resource_types=scenario["resource_types"],
            available=scenario["available"],
            allocation=scenario["allocation"],
            maximum=scenario["maximum"],
            process_names=scenario["process_names"],
        )
        initial_safe, initial_seq, initial_trace = self.kernel.resource_manager.check_safety()
        safe_req = self.kernel.resource_manager.request_resources(
            scenario["safe_request"]["process_index"],
            scenario["safe_request"]["request"],
        )
        unsafe_req = self.kernel.resource_manager.request_resources(
            scenario["unsafe_request"]["process_index"],
            scenario["unsafe_request"]["request"],
        )
        return {
            "mode": "DEMO",
            "initial_safe": initial_safe,
            "initial_sequence": initial_seq,
            "initial_trace": initial_trace,
            "safe_request_result": safe_req,
            "unsafe_request_result": unsafe_req,
        }

    def run_deadlock_demo(self) -> Dict[str, Any]:
        scenario = get_demo_deadlock_scenario()
        self.kernel.deadlock_manager.configure_scenario(
            resource_types=scenario["resource_types"],
            process_names=scenario["process_names"],
            available=scenario["available"],
            allocation=scenario["allocation"],
            request=scenario["request"],
        )
        rag = self.kernel.deadlock_manager.build_resource_allocation_graph()
        before = self.kernel.deadlock_manager.detect_deadlock()
        recovery = self.kernel.deadlock_manager.recover_by_terminating("P0")
        return {
            "mode": "DEMO",
            "rag": rag,
            "before_recovery": before,
            "recovery": recovery,
        }

    def run_real_job_demo(self) -> Dict[str, Any]:
        files = ensure_demo_input_files(self.kernel.config_manager.demo_dir)
        job_csv = self.kernel.process_manager.submit_job(
            name="DEMO_CSV_Summary",
            job_type="process_csv",
            priority=1,
            arrival_time=0,
            burst_time=2,
            memory_required=64,
            input_path=str(files["csv"]),
        )
        rec_csv = self.kernel.process_manager.execute_job(job_csv.job_id)

        job_script = self.kernel.process_manager.submit_job(
            name="DEMO_Python_Worker",
            job_type="run_python_script",
            priority=2,
            arrival_time=1,
            burst_time=3,
            memory_required=64,
            input_path=str(files["script"]),
        )
        rec_script = self.kernel.process_manager.execute_job(job_script.job_id)

        return {
            "mode": "DEMO (Real Subprocesses)",
            "jobs": [job_csv, job_script],
            "records": [rec_csv, rec_script],
        }

    def run_live_monitoring_demo(self) -> Dict[str, Any]:
        snapshot = self.kernel.system_monitor.get_system_snapshot()
        processes = self.kernel.system_monitor.list_host_processes(
            kernel_pids=self.kernel.process_manager.get_tracked_pids(),
            limit=10,
        )
        return {
            "mode": "LIVE",
            "snapshot": snapshot,
            "top_processes": processes,
        }

