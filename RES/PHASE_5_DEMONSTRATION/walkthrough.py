from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from RES.kernel import KernelEngine


def run_complete_walkthrough(kernel: "KernelEngine") -> Dict[str, Any]:
    demo = kernel.demo_engine
    real_jobs = demo.run_real_job_demo()
    scheduling = demo.run_scheduling_demo(quantum=kernel.config_manager.config.default_time_quantum)
    memory = demo.run_memory_demo()
    banker = demo.run_banker_demo()
    deadlock = demo.run_deadlock_demo()
    monitoring = demo.run_live_monitoring_demo()

    sections = {
        "1. REAL JOB EXECUTION (DEMO WORKLOAD)": [
            f"{rec.job_id}: {rec.outcome} (exit={rec.exit_code}, duration={rec.duration}s)"
            for rec in real_jobs["records"]
        ],
        "2. CPU SCHEDULING COMPARISON (DEMO)": [
            f"{algo}: AvgWait={rep.avg_waiting_time}, AvgTurnaround={rep.avg_turnaround_time}, AvgResp={rep.avg_response_time}"
            for algo, rep in scheduling["comparison"]["reports"].items()
        ],
        "3. MEMORY ALLOCATION COMPARISON (DEMO)": [
            f"{strat}: Succeeded={res['metrics']['allocations_succeeded']}, InternalFrag={res['metrics']['internal_fragmentation']} KB"
            for strat, res in memory["comparison"]["results"].items()
        ],
        "4. BANKER'S ALGORITHM (DEMO)": [
            f"Initial Safe: {banker['initial_safe']} | Sequence: {' -> '.join(banker['initial_sequence'])}",
            f"Safe Request: {banker['safe_request_result']['reason']}",
            f"Unsafe Request: {banker['unsafe_request_result']['reason']}",
        ],
        "5. DEADLOCK DETECTION & RECOVERY (DEMO)": [
            f"Before Recovery: {deadlock['before_recovery']['summary']}",
            f"After Terminating P0: {deadlock['recovery']['post_recovery_detection']['summary']}",
        ],
        "6. LIVE HOST SYSTEM MONITORING (LIVE)": [
            f"CPU: {monitoring['snapshot']['cpu_percent']}% | RAM: {monitoring['snapshot']['ram_percent']}% | Disk: {monitoring['snapshot']['disk_percent']}% | Status: {monitoring['snapshot']['status']}"
        ],
    }

    txt_report = kernel.analytics.export_text_report("complete_walkthrough", "Complete City Walkthrough", sections)
    json_report = kernel.analytics.export_json_report("complete_walkthrough", sections)
    kernel.logger.log_event("DEMO", "Completed full Kernel City walkthrough.")

    return {
        "real_jobs": real_jobs,
        "scheduling": scheduling,
        "memory": memory,
        "banker": banker,
        "deadlock": deadlock,
        "monitoring": monitoring,
        "text_report": str(txt_report),
        "json_report": str(json_report),
    }

