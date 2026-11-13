from typing import Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from GUI.widgets import (
    pause,
    prompt_int,
    prompt_text,
    render_gantt_chart,
    render_header,
    render_memory_blocks,
    run_export_menu,
)
from RES.kernel import KernelEngine
from RES.models import Job, JobState
from RES.PHASE_4_TESTING.error_handling import KernelCityError
from RES.PHASE_5_DEMONSTRATION.demo_datasets import get_demo_memory_scenario, get_demo_scheduling_jobs


def run_building(console: Console, kernel: KernelEngine, building_name: str) -> None:
    handlers = {
        "Job House": _building_job_house,
        "Scheduling Plaza": _building_scheduling_plaza,
        "Process Garage": _building_process_garage,
        "Memory Centre": _building_memory_centre,
        "Allocation Laboratory": _building_allocation_laboratory,
        "Memory Analytics Office": _building_memory_analytics_office,
        "Resource Allocation Office": _building_resource_office,
        "Banker's Algorithm Centre": _building_banker_centre,
        "Deadlock Court": _building_deadlock_court,
        "Analytics Hall": _building_analytics_hall,
        "History Museum": _building_history_museum,
        "Report Centre": _building_report_centre,
        "System Watchtower": _building_system_watchtower,
        "Storage Depot": _building_storage_depot,
    }
    handler = handlers.get(building_name)
    if handler:
        handler(console, kernel)


def _building_job_house(console: Console, kernel: KernelEngine) -> None:
    while True:
        console.clear()
        render_header(console, "JOB HOUSE", "Operations District — Process Registration & Queue")
        table = Table(border_style="blue")
        table.add_column("Key", style="bold yellow", width=6)
        table.add_column("Operation", style="bold white")
        table.add_row("1", "Register / Submit a New Job")
        table.add_row("2", "View & Filter Job Queue")
        table.add_row("3", "Inspect a Job")
        table.add_row("4", "Manage Existing Jobs (Execute / Cancel / Retry)")
        table.add_row("5", "View Execution Records")
        table.add_row("B", "Return to District")
        console.print(table)

        choice = prompt_text(console, "Select operation", "B").upper()
        if choice == "B":
            return
        try:
            if choice == "1":
                custom_id = prompt_text(console, "Job/Process ID (leave blank for auto)", "")
                name = prompt_text(console, "Job name")
                console.print(f"[info]Allowed types: {', '.join(kernel.process_manager.ALLOWED_JOB_TYPES)}[/info]")
                jtype = prompt_text(console, "Job type", "system_info_task")
                prio = prompt_int(console, "Priority (1=highest .. 10)", 2)
                arr = prompt_int(console, "Arrival time (>=0)", 0)
                burst = prompt_int(console, "Estimated CPU burst (>=1)", 3)
                mem = prompt_int(console, "Memory requirement (KB)", 64)
                if None in (prio, arr, burst, mem):
                    pause(console)
                    continue
                in_path = ""
                if jtype != "system_info_task":
                    console.print(f"[muted]Demo files available in: {kernel.config_manager.demo_dir}[/muted]")
                    in_path = prompt_text(console, "Input path (inside data/demo or data/jobs)")
                job = kernel.process_manager.submit_job(
                    name=name,
                    job_type=jtype,
                    priority=prio,
                    arrival_time=arr,
                    burst_time=burst,
                    memory_required=mem,
                    input_path=in_path or None,
                    job_id=custom_id or None,
                )
                console.print(f"[success]Registered {job.job_id} ({job.name}) in state {job.state.value}.[/success]")
            elif choice == "2":
                state_raw = prompt_text(console, "Filter by state (ALL, NEW, READY, RUNNING, WAITING, COMPLETED, TERMINATED, FAILED, CANCELLED)", "ALL").upper()
                state_filter = None if state_raw == "ALL" else JobState(state_raw)
                query = prompt_text(console, "Search text (ID/name/type, blank for all)", "")
                jobs = kernel.process_manager.filter_jobs(state_filter=state_filter, query=query)
                q_table = Table(title=f"Kernel City Job Queue ({len(jobs)} matching)", border_style="cyan")
                q_table.add_column("Job ID", style="bold white")
                q_table.add_column("Name")
                q_table.add_column("Type")
                q_table.add_column("State")
                q_table.add_column("Prio", justify="right")
                q_table.add_column("Arr", justify="right")
                q_table.add_column("Burst", justify="right")
                q_table.add_column("Mem(KB)", justify="right")
                for job in jobs:
                    q_table.add_row(
                        job.job_id, job.name, job.job_type, job.state.value,
                        str(job.priority), str(job.arrival_time), str(job.burst_time), str(job.memory_required),
                    )
                console.print(q_table)
            elif choice == "3":
                jid = prompt_text(console, "Enter Job ID (e.g. JOB-0001)").upper()
                job = kernel.process_manager.get_job(jid)
                console.print(Panel(
                    f"Job ID: {job.job_id}\nName: {job.name}\nType: {job.job_type}\n"
                    f"State: {job.state.value}\nPriority: {job.priority} | Arrival: {job.arrival_time} | Burst: {job.burst_time}\n"
                    f"Memory: {job.memory_required} KB\nInput: {job.input_path or '-'}\nOutput: {job.output_path or '-'}\n"
                    f"Submitted: {job.submission_timestamp}\nExit Status: {job.exit_status}\nError: {job.error_details or '-'}",
                    title=f"Job Inspection: {job.job_id}",
                    border_style="cyan",
                ))
            elif choice == "4":
                jid = prompt_text(console, "Enter Job ID").upper()
                action = prompt_text(console, "Action (E=Execute, C=Cancel, R=Retry)", "E").upper()
                if action == "E":
                    rec = kernel.process_manager.execute_job(jid)
                    console.print(f"[success]Executed {jid}: {rec.outcome} (exit={rec.exit_code}, {rec.duration}s)[/success]")
                elif action == "C":
                    job = kernel.process_manager.cancel_job(jid)
                    console.print(f"[warning]Job {job.job_id} is now {job.state.value}.[/warning]")
                elif action == "R":
                    rec = kernel.process_manager.retry_job(jid)
                    console.print(f"[success]Retried {jid}: {rec.outcome} (exit={rec.exit_code})[/success]")
                else:
                    console.print("[error]Invalid action.[/error]")
            elif choice == "5":
                records = kernel.db.get_execution_records(limit=25)
                rec_table = Table(title="Recent Execution Records", border_style="cyan")
                rec_table.add_column("Job ID")
                rec_table.add_column("Timestamp")
                rec_table.add_column("Outcome")
                rec_table.add_column("Exit", justify="right")
                rec_table.add_column("Duration(s)", justify="right")
                rec_table.add_column("Output")
                for rec in records:
                    rec_table.add_row(rec.job_id, rec.execution_timestamp, rec.outcome, str(rec.exit_code), str(rec.duration), rec.output_location or "-")
                console.print(rec_table)
                run_export_menu(
                    console,
                    "execution_history",
                    kernel.config_manager.reports_dir,
                    csv_fn=lambda fn, od, ov: kernel.analytics.export_history_csv(records, filename=fn, output_dir=od, overwrite=ov),
                )
                continue
        except (KernelCityError, ValueError) as exc:
            console.print(f"[error]{exc}[/error]")
        pause(console)


def _building_scheduling_plaza(console: Console, kernel: KernelEngine) -> None:
    quantum = kernel.config_manager.config.default_time_quantum
    manual_jobs: List[Job] = []
    while True:
        console.clear()
        render_header(
            console,
            "SCHEDULING PLAZA",
            "Operations District — CPU Scheduling, Manual Workloads & CSV Export",
            badge=f"Q={quantum} | MANUAL={len(manual_jobs)}",
        )
        table = Table(border_style="blue")
        table.add_column("Key", style="bold yellow", width=6)
        table.add_column("Operation", style="bold white")
        table.add_row("1", "Run Scheduling Algorithm (FCFS / SJF / PRIORITY / ROUND_ROBIN)")
        table.add_row("2", "Compare All 4 Algorithms on Same Workload")
        table.add_row("3", "Add / Clear Manual Workload Processes")
        table.add_row("4", "Configure Round Robin Time Quantum")
        table.add_row("B", "Return to District")
        console.print(table)

        choice = prompt_text(console, "Select operation", "B").upper()
        if choice == "B":
            return
        try:
            if choice == "3":
                sub = prompt_text(console, "M=Add manual process, C=Clear manual workload", "M").upper()
                if sub == "C":
                    manual_jobs.clear()
                    console.print("[warning]Manual workload cleared.[/warning]")
                else:
                    pid = prompt_text(console, "Process ID", f"M{len(manual_jobs) + 1}").upper()
                    pname = prompt_text(console, "Process Name", f"Task-{len(manual_jobs) + 1}")
                    arr = prompt_int(console, "Arrival time (>=0)", 0)
                    burst = prompt_int(console, "Burst time (>=1)", 4)
                    prio = prompt_int(console, "Priority (1=highest .. 10)", 2)
                    if None not in (arr, burst, prio):
                        if arr < 0 or burst < 1 or prio < 1:
                            raise KernelCityError("Arrival >= 0, Burst >= 1, Priority >= 1 required.")
                        manual_jobs.append(Job(job_id=pid, name=pname, job_type="system_info_task", priority=prio, arrival_time=arr, burst_time=burst))
                        console.print(f"[success]Added {pid} to manual workload.[/success]")
                pause(console)
                continue

            if choice in ("1", "2"):
                source_choice = prompt_text(console, "Workload: M=Manual, R=Registered Jobs, D=Demo Dataset", "D").upper()
                if source_choice == "M":
                    jobs = list(manual_jobs)
                elif source_choice == "R":
                    jobs = [j for j in kernel.process_manager.list_jobs() if j.state != JobState.CANCELLED]
                else:
                    jobs = get_demo_scheduling_jobs()

                if choice == "1":
                    algo = prompt_text(console, "Algorithm (FCFS, SJF, PRIORITY, ROUND_ROBIN)", "FCFS").upper()
                    report = kernel.scheduler.schedule(jobs, algorithm=algo, quantum=quantum)
                    kernel.db.record_scheduling_run(
                        algorithm=report.algorithm,
                        quantum=report.quantum,
                        job_count=len(report.entries),
                        avg_waiting=report.avg_waiting_time,
                        avg_turnaround=report.avg_turnaround_time,
                        avg_response=report.avg_response_time,
                        throughput=report.throughput,
                    )
                    res_table = Table(title=f"{report.algorithm} Results", border_style="cyan")
                    res_table.add_column("Job")
                    res_table.add_column("Arr", justify="right")
                    res_table.add_column("Burst", justify="right")
                    res_table.add_column("Prio", justify="right")
                    res_table.add_column("Comp", justify="right")
                    res_table.add_column("Turn", justify="right")
                    res_table.add_column("Wait", justify="right")
                    res_table.add_column("Resp", justify="right")
                    for e in report.entries:
                        res_table.add_row(
                            e.job_id, str(e.arrival_time), str(e.burst_time), str(e.priority),
                            str(e.completion_time), str(e.turnaround_time), str(e.waiting_time), str(e.response_time),
                        )
                    console.print(res_table)
                    render_gantt_chart(console, report.gantt_chart)
                    console.print(
                        f"[success]Avg Waiting: {report.avg_waiting_time} | Avg Turnaround: {report.avg_turnaround_time} | "
                        f"Avg Response: {report.avg_response_time} | Throughput: {report.throughput}[/success]"
                    )
                    run_export_menu(
                        console,
                        f"scheduling_{report.algorithm.lower()}",
                        kernel.config_manager.reports_dir,
                        csv_fn=lambda fn, od, ov: kernel.analytics.export_scheduling_csv(report, filename=fn, output_dir=od, overwrite=ov),
                        json_fn=lambda fn, od, ov: kernel.analytics.export_json_report(fn, {"report": report}, output_dir=od, overwrite=ov, use_timestamp=False),
                        chart_fn=lambda: kernel.analytics.charts.generate_gantt_chart_png(report),
                    )
                    continue
                else:
                    comp = kernel.analytics.run_scheduling_analysis(kernel.scheduler, jobs, quantum=quantum)
                    cmp_table = Table(title="Algorithm Comparison", border_style="cyan")
                    cmp_table.add_column("Algorithm", style="bold white")
                    cmp_table.add_column("Avg Waiting", justify="right")
                    cmp_table.add_column("Avg Turnaround", justify="right")
                    cmp_table.add_column("Avg Response", justify="right")
                    cmp_table.add_column("Throughput", justify="right")
                    for algo_name, rep in comp["reports"].items():
                        cmp_table.add_row(
                            algo_name, f"{rep.avg_waiting_time:.3f}", f"{rep.avg_turnaround_time:.3f}",
                            f"{rep.avg_response_time:.3f}", f"{rep.throughput:.4f}",
                        )
                    console.print(cmp_table)
                    for obs in comp["observations"]:
                        console.print(f"[info]- {obs}[/info]")
                    run_export_menu(
                        console,
                        "scheduling_comparison",
                        kernel.config_manager.reports_dir,
                        csv_fn=lambda fn, od, ov: kernel.analytics.export_scheduling_comparison_csv(comp, filename=fn, output_dir=od, overwrite=ov),
                        json_fn=lambda fn, od, ov: kernel.analytics.export_json_report(fn, comp, output_dir=od, overwrite=ov, use_timestamp=False),
                        chart_fn=lambda: kernel.analytics.charts.generate_scheduling_comparison_chart(comp["reports"]),
                    )
                    continue
            elif choice == "4":
                new_q = prompt_int(console, "New Time Quantum (>=1)", quantum)
                if new_q is not None and new_q >= 1:
                    quantum = new_q
                    console.print(f"[success]Time quantum set to {quantum}.[/success]")
        except KernelCityError as exc:
            console.print(f"[error]{exc}[/error]")
        pause(console)


def _building_process_garage(console: Console, kernel: KernelEngine) -> None:
    query = ""
    while True:
        console.clear()
        render_header(console, "PROCESS GARAGE", "Operations District — Application Subprocess Tracker")
        procs = kernel.process_manager.list_process_infos()
        if query:
            procs = [p for p in procs if query.lower() in p.job_id.lower() or query == str(p.host_pid)]
        table = Table(title=f"Tracked Subprocesses (Filter: '{query or 'ALL'}')", border_style="cyan")
        table.add_column("Job ID", style="bold white")
        table.add_column("Host PID", justify="right")
        table.add_column("Status")
        table.add_column("Exit", justify="right")
        table.add_column("Duration(s)", justify="right")
        table.add_column("Start Time")
        for p in procs:
            table.add_row(
                p.job_id, str(p.host_pid or "-"), p.process_status,
                str(p.exit_code if p.exit_code is not None else "-"),
                str(p.duration_seconds), p.start_time or "-",
            )
        console.print(table)
        console.print("\n[nav]S=Search PID/Job | I=Inspect Job | C=Cancel/Terminate | B=Return to District[/nav]")
        choice = prompt_text(console, "Action", "B").upper()
        if choice == "B":
            return
        if choice == "S":
            query = prompt_text(console, "Search Job ID or PID (blank to clear)", "")
            continue
        if choice == "I":
            jid = prompt_text(console, "Job ID to inspect").upper()
            try:
                job = kernel.process_manager.get_job(jid)
                console.print(f"[info]{job.job_id} | {job.name} | State={job.state.value} | Exit={job.exit_status} | Output={job.output_path}[/info]")
            except KernelCityError as exc:
                console.print(f"[error]{exc}[/error]")
            pause(console)
        elif choice == "C":
            jid = prompt_text(console, "Job ID to cancel").upper()
            try:
                job = kernel.process_manager.cancel_job(jid)
                console.print(f"[warning]Job {job.job_id} marked {job.state.value}.[/warning]")
            except KernelCityError as exc:
                console.print(f"[error]{exc}[/error]")
            pause(console)


def _building_memory_centre(console: Console, kernel: KernelEngine) -> None:
    while True:
        console.clear()
        render_header(console, "MEMORY CENTRE", "Memory District — Pool Creation & Partition Allocation")
        render_memory_blocks(console, kernel.memory_manager.blocks)
        metrics = kernel.memory_manager.get_metrics()
        console.print(
            f"[info]Total: {metrics['total_memory']} KB | Allocated: {metrics['allocated_memory']} KB | "
            f"Free: {metrics['free_memory']} KB ({metrics['free_blocks_count']} blocks) | "
            f"Internal Frag: {metrics['internal_fragmentation']} KB | External Frag: {metrics['external_fragmentation']} KB[/info]"
        )
        console.print(f"[muted]{kernel.memory_manager.get_fragmentation_explanation()}[/muted]")

        console.print("\n[nav]1=Allocate | 2=Deallocate | 3=Create Pool (Total+Partitions) | 4=Reset | 5=Export CSV | B=Back[/nav]")
        choice = prompt_text(console, "Select action", "B").upper()
        if choice == "B":
            return
        try:
            if choice == "1":
                ref = prompt_text(console, "Process/Job identifier", "P1")
                size = prompt_int(console, "Requested size (KB)", 128)
                strat = prompt_text(console, "Strategy (FIRST_FIT, BEST_FIT, WORST_FIT)", "FIRST_FIT").upper()
                if size is not None:
                    rec = kernel.memory_manager.allocate(ref, size, strategy=strat)
                    kernel.db.record_memory_event(
                        strategy=rec.strategy, reference=rec.reference, requested_size=rec.requested_size,
                        allocated_block_id=rec.allocated_block_id, remaining_free=rec.remaining_free_space, status=rec.status,
                    )
                    if rec.status == "ALLOCATED":
                        console.print(f"[success]Allocated {rec.requested_size} KB to {rec.reference} in block {rec.allocated_block_id}.[/success]")
                    else:
                        console.print(f"[warning]Allocation FAILED for {rec.reference} ({rec.requested_size} KB).[/warning]")
            elif choice == "2":
                target = prompt_text(console, "Process reference or Block ID to free")
                if kernel.memory_manager.deallocate(target):
                    console.print(f"[success]Deallocated {target}.[/success]")
                else:
                    console.print(f"[warning]No active allocation matched '{target}'.[/warning]")
            elif choice == "3":
                total = prompt_int(console, "Total memory pool size (KB)", 1000)
                raw = prompt_text(console, "Comma-separated partition sizes (KB)", "100,250,300,350")
                sizes = [int(x.strip()) for x in raw.split(",") if x.strip()]
                if total is not None:
                    kernel.memory_manager.create_pool_from_total(total, sizes)
                    console.print("[success]Memory pool created.[/success]")
            elif choice == "4":
                kernel.memory_manager.configure_blocks([100, 250, 300, 350])
                console.print("[success]Memory model reset to default partitions.[/success]")
            elif choice == "5":
                run_export_menu(
                    console,
                    "memory_allocations",
                    kernel.config_manager.reports_dir,
                    csv_fn=lambda fn, od, ov: kernel.analytics.export_memory_csv(
                        kernel.memory_manager.history,
                        kernel.memory_manager.blocks,
                        kernel.memory_manager.get_metrics(),
                        filename=fn,
                        output_dir=od,
                        overwrite=ov,
                    ),
                )
                continue
        except (KernelCityError, ValueError) as exc:
            console.print(f"[error]{exc}[/error]")
        pause(console)


def _building_allocation_laboratory(console: Console, kernel: KernelEngine) -> None:
    scenario = get_demo_memory_scenario()
    block_sizes = list(scenario["block_sizes"])
    requests = list(scenario["requests"])
    while True:
        console.clear()
        render_header(console, "ALLOCATION LABORATORY", "Memory District — Controlled Strategy Comparison")
        console.print(f"[info]Current Blocks (KB):[/info] {block_sizes}")
        console.print(f"[info]Current Requests:[/info] {[(r['reference'], r['size']) for r in requests]}")
        console.print("\n[nav]1=Run All-Strategy Comparison | 2=Modify Blocks | 3=Add Request | 4=Reset Demo Dataset | B=Back[/nav]")
        choice = prompt_text(console, "Select action", "B").upper()
        if choice == "B":
            return
        try:
            if choice == "1":
                comp = kernel.analytics.run_memory_analysis(kernel.memory_manager, block_sizes, requests)
                cmp_table = Table(title="Memory Strategy Comparison (Independent Pool Copies)", border_style="cyan")
                cmp_table.add_column("Strategy")
                cmp_table.add_column("Succeeded", justify="right")
                cmp_table.add_column("Failed", justify="right")
                cmp_table.add_column("Allocated (KB)", justify="right")
                cmp_table.add_column("Internal Frag (KB)", justify="right")
                cmp_table.add_column("External Frag (KB)", justify="right")
                for strat, data in comp["results"].items():
                    m = data["metrics"]
                    cmp_table.add_row(
                        strat, str(m["allocations_succeeded"]), str(m["allocations_failed"]),
                        str(m["allocated_memory"]), str(m["internal_fragmentation"]), str(m["external_fragmentation"]),
                    )
                console.print(cmp_table)
                for obs in comp["observations"]:
                    console.print(f"[info]- {obs}[/info]")
                run_export_menu(
                    console,
                    "memory_comparison",
                    kernel.config_manager.reports_dir,
                    csv_fn=lambda fn, od, ov: kernel.analytics.export_memory_comparison_csv(comp, filename=fn, output_dir=od, overwrite=ov),
                    json_fn=lambda fn, od, ov: kernel.analytics.export_json_report(fn, comp, output_dir=od, overwrite=ov, use_timestamp=False),
                    chart_fn=lambda: kernel.analytics.charts.generate_memory_comparison_chart(comp["results"]),
                )
                continue
            elif choice == "2":
                raw = prompt_text(console, "Comma-separated block sizes (KB)", "100,500,200,300,600")
                parsed = [int(x.strip()) for x in raw.split(",") if x.strip()]
                if not parsed or any(x <= 0 for x in parsed):
                    raise KernelCityError("All block sizes must be > 0.")
                block_sizes = parsed
            elif choice == "3":
                ref = prompt_text(console, "Request process reference", f"PROC-{len(requests) + 1}")
                size = prompt_int(console, "Size (KB)", 150)
                if size is not None and size > 0:
                    requests.append({"reference": ref, "size": size})
            elif choice == "4":
                scenario = get_demo_memory_scenario()
                block_sizes = list(scenario["block_sizes"])
                requests = list(scenario["requests"])
        except (KernelCityError, ValueError) as exc:
            console.print(f"[error]{exc}[/error]")
        pause(console)


def _building_memory_analytics_office(console: Console, kernel: KernelEngine) -> None:
    while True:
        console.clear()
        render_header(console, "MEMORY ANALYTICS OFFICE", "Memory District — Fragmentation & History Analysis")
        metrics = kernel.memory_manager.get_metrics()
        events = kernel.db.get_memory_events(limit=15)
        console.print(Panel(
            f"Total Pool: {metrics['total_memory']} KB\n"
            f"Requested: {metrics['requested_memory']} KB | Allocated: {metrics['allocated_memory']} KB\n"
            f"Free Memory: {metrics['free_memory']} KB across {metrics['free_blocks_count']} free blocks\n"
            f"Internal Fragmentation: {metrics['internal_fragmentation']} KB\n"
            f"External Fragmentation: {metrics['external_fragmentation']} KB\n"
            f"Success / Failure: {metrics['allocations_succeeded']} / {metrics['allocations_failed']}",
            title="Live Pool Metrics",
            border_style="cyan",
        ))
        table = Table(title="Recent Persistent Memory Events", border_style="blue")
        table.add_column("Timestamp")
        table.add_column("Strategy")
        table.add_column("Reference")
        table.add_column("Requested (KB)", justify="right")
        table.add_column("Block")
        table.add_column("Status")
        for ev in events:
            table.add_row(ev["timestamp"], ev["strategy"], ev["reference"], str(ev["requested_size"]), ev["allocated_block_id"] or "-", ev["status"])
        console.print(table)
        console.print("\n[nav]1=Export Current Pool CSV | B=Back[/nav]")
        choice = prompt_text(console, "Select action", "B").upper()
        if choice == "B":
            return
        if choice == "1":
            run_export_menu(
                console,
                "memory_analytics",
                kernel.config_manager.reports_dir,
                csv_fn=lambda fn, od, ov: kernel.analytics.export_memory_csv(
                    kernel.memory_manager.history,
                    kernel.memory_manager.blocks,
                    metrics,
                    filename=fn,
                    output_dir=od,
                    overwrite=ov,
                ),
            )


def _building_resource_office(console: Console, kernel: KernelEngine) -> None:
    while True:
        console.clear()
        render_header(console, "RESOURCE ALLOCATION OFFICE", "Resource District — Resource Model & Matrices")
        state = kernel.resource_manager.state
        table = Table(title=f"Available: {state.available} ({', '.join(state.resource_types)})", border_style="cyan")
        table.add_column("Process", style="bold white")
        table.add_column("Allocation")
        table.add_column("Maximum")
        table.add_column("Need (Max - Alloc)")
        for idx, pname in enumerate(state.process_names):
            table.add_row(pname, str(state.allocation[idx]), str(state.maximum[idx]), str(state.need[idx]))
        console.print(table)

        console.print("\n[nav]1=Create Custom Resource Model | 2=Reset Default Model | 3=Export CSV | B=Back[/nav]")
        choice = prompt_text(console, "Select action", "B").upper()
        if choice == "B":
            return
        try:
            if choice == "1":
                r_raw = prompt_text(console, "Resource type names (comma-separated)", "R0,R1,R2")
                r_types = [x.strip() for x in r_raw.split(",") if x.strip()]
                a_raw = prompt_text(console, f"Available instances ({len(r_types)} ints)", "3,3,2")
                available = [int(x.strip()) for x in a_raw.split(",")]
                n_procs = prompt_int(console, "Number of processes (1..10)", 3)
                if n_procs is None or n_procs < 1:
                    raise KernelCityError("Number of processes must be >= 1.")
                alloc: List[List[int]] = []
                maximum: List[List[int]] = []
                names: List[str] = []
                for i in range(n_procs):
                    names.append(f"P{i}")
                    row_a = prompt_text(console, f"P{i} Allocation ({len(r_types)} ints)", ",".join(["0"] * len(r_types)))
                    row_m = prompt_text(console, f"P{i} Maximum ({len(r_types)} ints)", ",".join(["1"] * len(r_types)))
                    alloc.append([int(x.strip()) for x in row_a.split(",")])
                    maximum.append([int(x.strip()) for x in row_m.split(",")])
                kernel.resource_manager.configure_state(r_types, available, alloc, maximum, process_names=names)
                console.print("[success]Custom resource model configured.[/success]")
            elif choice == "2":
                kernel.resource_manager.state = kernel.resource_manager.create_default_state()
                console.print("[success]Default resource model restored.[/success]")
            elif choice == "3":
                is_safe, seq, _ = kernel.resource_manager.check_safety()
                run_export_menu(
                    console,
                    "resource_allocation",
                    kernel.config_manager.reports_dir,
                    csv_fn=lambda fn, od, ov: kernel.analytics.export_resource_allocation_csv(
                        kernel.resource_manager.state,
                        is_safe,
                        seq,
                        filename=fn,
                        output_dir=od,
                        overwrite=ov,
                    ),
                )
                continue
        except (KernelCityError, ValueError) as exc:
            console.print(f"[error]{exc}[/error]")
        pause(console)


def _building_banker_centre(console: Console, kernel: KernelEngine) -> None:
    last_request: Optional[List[int]] = None
    while True:
        console.clear()
        render_header(console, "BANKER'S ALGORITHM CENTRE", "Resource District — Safety Checks & Resource Requests")
        state = kernel.resource_manager.state
        table = Table(title=f"Available: {state.available} ({', '.join(state.resource_types)})", border_style="cyan")
        table.add_column("Process", style="bold white")
        table.add_column("Allocation")
        table.add_column("Maximum")
        table.add_column("Need (Max - Alloc)")
        for idx, pname in enumerate(state.process_names):
            table.add_row(pname, str(state.allocation[idx]), str(state.maximum[idx]), str(state.need[idx]))
        console.print(table)

        console.print("\n[nav]1=Run Safety Check | 2=Submit Resource Request | 3=Reset Default | 4=Export CSV | B=Back[/nav]")
        choice = prompt_text(console, "Select action", "B").upper()
        if choice == "B":
            return
        try:
            if choice == "1":
                is_safe, seq, trace = kernel.resource_manager.check_safety()
                if is_safe:
                    console.print(f"[success]SAFE STATE: {' -> '.join(seq)}[/success]")
                else:
                    console.print("[error]UNSAFE STATE: No safe sequence exists (risk of deadlock if processes request full max).[/error]")
                for step in trace:
                    console.print(f"  [muted]{step}[/muted]")
            elif choice == "2":
                p_idx = prompt_int(console, f"Process index (0..{len(state.process_names) - 1})", 1)
                raw_vec = prompt_text(console, f"Request vector ({len(state.available)} comma-separated ints)", "1,0,2")
                vec = [int(x.strip()) for x in raw_vec.split(",")]
                if p_idx is not None:
                    last_request = vec
                    res = kernel.resource_manager.request_resources(p_idx, vec)
                    style = "success" if res["granted"] else "warning"
                    console.print(f"[{style}]{res['reason']}[/{style}]")
                    if res["safe_sequence"]:
                        console.print(f"[info]Safe Sequence: {' -> '.join(res['safe_sequence'])}[/info]")
            elif choice == "3":
                kernel.resource_manager.state = kernel.resource_manager.create_default_state()
                last_request = None
                console.print("[success]Resource state reset to default.[/success]")
            elif choice == "4":
                is_safe, seq, _ = kernel.resource_manager.check_safety()
                run_export_menu(
                    console,
                    "banker_safety",
                    kernel.config_manager.reports_dir,
                    csv_fn=lambda fn, od, ov: kernel.analytics.export_resource_allocation_csv(
                        kernel.resource_manager.state,
                        is_safe,
                        seq,
                        last_request=last_request,
                        filename=fn,
                        output_dir=od,
                        overwrite=ov,
                    ),
                )
                continue
        except (KernelCityError, ValueError) as exc:
            console.print(f"[error]{exc}[/error]")
        pause(console)


def _building_deadlock_court(console: Console, kernel: KernelEngine) -> None:
    last_recovery = ""
    while True:
        console.clear()
        render_header(console, "DEADLOCK COURT", "Resource District — Detection, RAG & Recovery")
        dm = kernel.deadlock_manager
        table = Table(title=f"Available: {dm.available} ({', '.join(dm.resource_types)})", border_style="cyan")
        table.add_column("Process")
        table.add_column("Allocation")
        table.add_column("Request")
        for idx, pname in enumerate(dm.process_names):
            table.add_row(pname, str(dm.allocation[idx]), str(dm.request[idx]))
        console.print(table)

        console.print("\n[nav]1=Run Detection | 2=RAG & Conditions | 3=Modify Request | 4=Recover | 5=Reset | 6=Export CSV | B=Back[/nav]")
        choice = prompt_text(console, "Select action", "B").upper()
        if choice == "B":
            return
        try:
            if choice == "1":
                res = dm.detect_deadlock()
                style = "error" if res["deadlocked"] else "success"
                console.print(f"[{style}]{res['summary']}[/{style}]")
                for line in res["trace"]:
                    console.print(f"  [muted]{line}[/muted]")
            elif choice == "2":
                console.print("[info]Four Necessary Conditions for Deadlock:[/info]")
                for cond in dm.NECESSARY_CONDITIONS:
                    console.print(f"  - {cond}")
                rag = dm.build_resource_allocation_graph()
                console.print("[info]Assignment Edges (Resource -> Process):[/info]")
                for e in rag["assignment_edges"]:
                    console.print(f"  {e}")
                console.print("[info]Request Edges (Process -> Resource):[/info]")
                for e in rag["request_edges"]:
                    console.print(f"  {e}")
            elif choice == "3":
                p_idx = prompt_int(console, f"Process index to edit (0..{len(dm.process_names) - 1})", 0)
                if p_idx is not None and 0 <= p_idx < len(dm.process_names):
                    req_raw = prompt_text(console, f"New Request vector ({len(dm.resource_types)} ints)", "0,0,0")
                    new_req = [int(x.strip()) for x in req_raw.split(",")]
                    updated_req = list(dm.request)
                    updated_req[p_idx] = new_req
                    dm.configure_scenario(dm.resource_types, dm.process_names, dm.available, dm.allocation, updated_req)
                    console.print(f"[success]Updated request for {dm.process_names[p_idx]}.[/success]")
                else:
                    raise KernelCityError("Invalid process index.")
            elif choice == "4":
                target = prompt_text(console, f"Process to terminate ({', '.join(dm.process_names)})", dm.process_names[0])
                rec = dm.recover_by_terminating(target)
                last_recovery = f"Terminated {rec['terminated_process']}, released {rec['released_resources']}"
                console.print(f"[warning]{last_recovery}[/warning]")
                console.print(f"[info]{rec['post_recovery_detection']['summary']}[/info]")
            elif choice == "5":
                dm.reset_default_scenario()
                last_recovery = ""
                console.print("[success]Deadlock scenario reset.[/success]")
            elif choice == "6":
                det = dm.detect_deadlock()
                run_export_menu(
                    console,
                    "deadlock_analysis",
                    kernel.config_manager.reports_dir,
                    csv_fn=lambda fn, od, ov: kernel.analytics.export_deadlock_csv(
                        dm.process_names,
                        dm.resource_types,
                        dm.allocation,
                        dm.request,
                        det,
                        recovery_summary=last_recovery,
                        filename=fn,
                        output_dir=od,
                        overwrite=ov,
                    ),
                )
                continue
        except (KernelCityError, ValueError) as exc:
            console.print(f"[error]{exc}[/error]")
        pause(console)


def _building_analytics_hall(console: Console, kernel: KernelEngine) -> None:
    while True:
        console.clear()
        render_header(console, "ANALYTICS HALL", "Intelligence District — Core Module Comparisons & Charts")
        console.print("[nav]1=Scheduling Comparison | 2=Memory Comparison | 3=Resource Safety Summary | B=Back[/nav]")
        choice = prompt_text(console, "Select action", "B").upper()
        if choice == "B":
            return
        try:
            if choice == "1":
                jobs = [j for j in kernel.process_manager.list_jobs() if j.state != JobState.CANCELLED]
                if not jobs:
                    jobs = get_demo_scheduling_jobs()
                    console.print("[info]Using DEMO scheduling workload (no registered jobs).[/info]")
                comp = kernel.analytics.run_scheduling_analysis(
                    kernel.scheduler, jobs, quantum=kernel.config_manager.config.default_time_quantum
                )
                for algo, rep in comp["reports"].items():
                    console.print(f"{algo}: AvgWait={rep.avg_waiting_time}, AvgTurn={rep.avg_turnaround_time}, AvgResp={rep.avg_response_time}")
                for obs in comp["observations"]:
                    console.print(f"[info]- {obs}[/info]")
                run_export_menu(
                    console,
                    "analytics_scheduling",
                    kernel.config_manager.reports_dir,
                    csv_fn=lambda fn, od, ov: kernel.analytics.export_scheduling_comparison_csv(comp, filename=fn, output_dir=od, overwrite=ov),
                    json_fn=lambda fn, od, ov: kernel.analytics.export_json_report(fn, comp, output_dir=od, overwrite=ov, use_timestamp=False),
                    chart_fn=lambda: kernel.analytics.charts.generate_scheduling_comparison_chart(comp["reports"]),
                )
                continue
            elif choice == "2":
                scenario = get_demo_memory_scenario()
                comp = kernel.analytics.run_memory_analysis(kernel.memory_manager, scenario["block_sizes"], scenario["requests"])
                for strat, data in comp["results"].items():
                    m = data["metrics"]
                    console.print(f"{strat}: Succeeded={m['allocations_succeeded']}, InternalFrag={m['internal_fragmentation']} KB")
                for obs in comp["observations"]:
                    console.print(f"[info]- {obs}[/info]")
                run_export_menu(
                    console,
                    "analytics_memory",
                    kernel.config_manager.reports_dir,
                    csv_fn=lambda fn, od, ov: kernel.analytics.export_memory_comparison_csv(comp, filename=fn, output_dir=od, overwrite=ov),
                    json_fn=lambda fn, od, ov: kernel.analytics.export_json_report(fn, comp, output_dir=od, overwrite=ov, use_timestamp=False),
                    chart_fn=lambda: kernel.analytics.charts.generate_memory_comparison_chart(comp["results"]),
                )
                continue
            elif choice == "3":
                is_safe, seq, _ = kernel.resource_manager.check_safety()
                det = kernel.deadlock_manager.detect_deadlock()
                console.print(f"[info]Banker's State Safe: {is_safe} | Sequence: {' -> '.join(seq)}[/info]")
                console.print(f"[info]Deadlock Court Status: {det['summary']}[/info]")
        except KernelCityError as exc:
            console.print(f"[error]{exc}[/error]")
        pause(console)


def _building_history_museum(console: Console, kernel: KernelEngine) -> None:
    while True:
        console.clear()
        render_header(console, "HISTORY MUSEUM", "Intelligence District — Searchable SQLite Archive")
        console.print("[nav]1=Search/Filter Execution History | 2=System Events | 3=Scheduling Runs | 4=Memory Events | B=Back[/nav]")
        choice = prompt_text(console, "Select archive", "B").upper()
        if choice == "B":
            return
        if choice == "1":
            status_filter = prompt_text(console, "Filter outcome (ALL, COMPLETED, FAILED)", "ALL").upper()
            date_filter = prompt_text(console, "Filter date prefix (e.g. 2026-11-13 or blank)", "")
            records = kernel.db.get_execution_records(limit=100)
            if status_filter != "ALL":
                records = [r for r in records if r.outcome.upper() == status_filter]
            if date_filter:
                records = [r for r in records if r.execution_timestamp.startswith(date_filter)]
            table = Table(title=f"Execution History ({len(records)} records)", border_style="cyan")
            table.add_column("Job ID")
            table.add_column("Timestamp")
            table.add_column("Outcome")
            table.add_column("Duration(s)", justify="right")
            for r in records[:25]:
                table.add_row(r.job_id, r.execution_timestamp, r.outcome, str(r.duration))
            console.print(table)
            run_export_menu(
                console,
                "filtered_execution_history",
                kernel.config_manager.reports_dir,
                csv_fn=lambda fn, od, ov: kernel.analytics.export_history_csv(records, filename=fn, output_dir=od, overwrite=ov),
            )
            continue
        elif choice == "2":
            events = kernel.db.get_events(limit=25)
            table = Table(title="Recorded Events", border_style="cyan")
            table.add_column("Timestamp")
            table.add_column("Category")
            table.add_column("Level")
            table.add_column("Message")
            for ev in events:
                table.add_row(ev["timestamp"], ev["category"], ev["level"], ev["message"])
            console.print(table)
        elif choice == "3":
            runs = kernel.db.get_scheduling_runs(limit=25)
            table = Table(title="Scheduling Runs", border_style="cyan")
            table.add_column("Timestamp")
            table.add_column("Algorithm")
            table.add_column("Avg Wait", justify="right")
            table.add_column("Avg Turn", justify="right")
            for r in runs:
                table.add_row(r["timestamp"], r["algorithm"], str(r["avg_waiting"]), str(r["avg_turnaround"]))
            console.print(table)
        elif choice == "4":
            mem_events = kernel.db.get_memory_events(limit=25)
            table = Table(title="Memory Allocation Events", border_style="cyan")
            table.add_column("Timestamp")
            table.add_column("Strategy")
            table.add_column("Ref")
            table.add_column("Size", justify="right")
            table.add_column("Status")
            for m in mem_events:
                table.add_row(m["timestamp"], m["strategy"], m["reference"], str(m["requested_size"]), m["status"])
            console.print(table)
        pause(console)


def _building_report_centre(console: Console, kernel: KernelEngine) -> None:
    while True:
        console.clear()
        render_header(console, "REPORT CENTRE", "Intelligence District — Central CSV, JSON, TXT & Experiment Exports")
        console.print(
            "[nav]1=Complete Activity (TXT + JSON) | 2=Execution History (CSV) | "
            "3=Complete Scheduling Experiment (CSV + Chart) | 4=System Snapshot (CSV + JSON) | B=Back[/nav]"
        )
        choice = prompt_text(console, "Select export", "B").upper()
        if choice == "B":
            return
        if choice == "1":
            jobs = kernel.process_manager.list_jobs()
            events = kernel.db.get_events(limit=20)
            snap = kernel.system_monitor.get_system_snapshot()
            sections: Dict[str, List[str]] = {
                "REGISTERED JOBS": [f"{j.job_id} | {j.name} | {j.job_type} | {j.state.value}" for j in jobs],
                "LIVE SYSTEM SNAPSHOT": [f"CPU={snap['cpu_percent']}% | RAM={snap['ram_percent']}% | Disk={snap['disk_percent']}% | Status={snap['status']}"],
                "RECENT EVENTS": [f"[{e['timestamp']}] {e['category']}: {e['message']}" for e in events],
            }
            txt_path = kernel.analytics.export_text_report("kernel_city_activity", "Complete Kernel City Activity", sections)
            json_path = kernel.analytics.export_json_report("kernel_city_activity", sections)
            kernel.logger.log_event("REPORT", f"Exported activity reports: {txt_path.name}, {json_path.name}")
            console.print(f"[success]Text report: {txt_path}[/success]")
            console.print(f"[success]JSON report: {json_path}[/success]")
        elif choice == "2":
            records = kernel.db.get_execution_records(limit=100)
            run_export_menu(
                console,
                "execution_records",
                kernel.config_manager.reports_dir,
                csv_fn=lambda fn, od, ov: kernel.analytics.export_history_csv(records, filename=fn, output_dir=od, overwrite=ov),
            )
            continue
        elif choice == "3":
            jobs = get_demo_scheduling_jobs()
            comp = kernel.analytics.run_scheduling_analysis(kernel.scheduler, jobs, quantum=kernel.config_manager.config.default_time_quantum)
            csv_path = kernel.analytics.export_scheduling_comparison_csv(comp)
            chart_path = kernel.analytics.charts.generate_scheduling_comparison_chart(comp["reports"])
            json_path = kernel.analytics.export_json_report("scheduling_experiment", {"jobs": jobs, "comparison": comp})
            console.print(f"[success]Experiment CSV: {csv_path}[/success]")
            console.print(f"[success]Experiment JSON: {json_path}[/success]")
            console.print(f"[success]Experiment Chart: {chart_path}[/success]")
        elif choice == "4":
            snap = kernel.system_monitor.get_system_snapshot()
            run_export_menu(
                console,
                "system_monitoring",
                kernel.config_manager.reports_dir,
                csv_fn=lambda fn, od, ov: kernel.analytics.export_monitoring_csv([snap], filename=fn, output_dir=od, overwrite=ov),
                json_fn=lambda fn, od, ov: kernel.analytics.export_json_report(fn, snap, output_dir=od, overwrite=ov, use_timestamp=False),
            )
            continue
        pause(console)


def _building_system_watchtower(console: Console, kernel: KernelEngine) -> None:
    collected: List[Dict[str, object]] = []
    while True:
        console.clear()
        snap = kernel.system_monitor.get_system_snapshot()
        collected.append(snap)
        render_header(console, "SYSTEM WATCHTOWER", "Intelligence District — Lightweight Host Telemetry", badge=snap["source"])
        status_style = "warning" if snap["warnings"] else "success"
        console.print(Panel(
            f"Timestamp: {snap['timestamp']}\n"
            f"CPU Usage: {snap['cpu_percent']}% ({snap['cpu_count_logical']} logical cores)\n"
            f"RAM Usage: {snap['ram_percent']}% ({snap['ram_used_gb']} / {snap['ram_total_gb']} GB, Available: {snap['ram_available_gb']} GB)\n"
            f"Disk Usage: {snap['disk_percent']}% (Free: {snap['disk_free_gb']} / {snap['disk_total_gb']} GB)\n"
            f"Active Processes: {snap['active_processes']}\n"
            f"System Status: [{status_style}]{snap['status']}[/{status_style}]",
            border_style="cyan",
        ))
        for warn in snap["warnings"]:
            console.print(f"[warning]ALERT: {warn}[/warning]")

        console.print("\n[nav]R=Refresh | I=Inspect PID | C=Configure Thresholds | E=Export Monitoring CSV | B=Back[/nav]")
        choice = prompt_text(console, "Select action", "B").upper()
        if choice == "B":
            return
        if choice == "I":
            pid = prompt_int(console, "PID to inspect")
            if pid is not None:
                try:
                    info = kernel.system_monitor.inspect_process(pid, kernel_pids=kernel.process_manager.get_tracked_pids())
                    console.print(f"[info]PID {info['pid']} ({info['name']}): status={info['status']}, CPU={info['cpu_percent']}%, RAM={info['memory_mb']} MB[/info]")
                except KernelCityError as exc:
                    console.print(f"[error]{exc}[/error]")
            pause(console)
        elif choice == "C":
            cpu_t = prompt_int(console, "CPU threshold (%)", int(kernel.system_monitor.cpu_threshold))
            ram_t = prompt_int(console, "RAM threshold (%)", int(kernel.system_monitor.ram_threshold))
            if cpu_t is not None and ram_t is not None:
                kernel.system_monitor.update_thresholds(float(cpu_t), float(ram_t), kernel.system_monitor.disk_threshold)
                kernel.config_manager.update(cpu_warning_threshold=float(cpu_t), ram_warning_threshold=float(ram_t))
        elif choice == "E":
            run_export_menu(
                console,
                "system_monitoring",
                kernel.config_manager.reports_dir,
                csv_fn=lambda fn, od, ov: kernel.analytics.export_monitoring_csv(collected, filename=fn, output_dir=od, overwrite=ov),
            )


def _building_storage_depot(console: Console, kernel: KernelEngine) -> None:
    while True:
        console.clear()
        render_header(console, "STORAGE DEPOT", "Intelligence District — Supporting Storage & File Inspector")
        summary = kernel.storage_manager.get_storage_summary()
        s_table = Table(title="Storage Consumption", border_style="cyan")
        s_table.add_column("Area", style="bold white")
        s_table.add_column("Files", justify="right")
        s_table.add_column("Total Size (KB)", justify="right")
        s_table.add_column("Path")
        for area, info in summary.items():
            s_table.add_row(area, str(info["file_count"]), str(info["total_kb"]), info["path"])
        console.print(s_table)

        console.print("\n[nav]1=List Files | 2=Inspect File | 3=Delete Temp File | B=Back[/nav]")
        choice = prompt_text(console, "Select action", "B").upper()
        if choice == "B":
            return
        try:
            if choice == "1":
                area = prompt_text(console, "Area (jobs, demo, reports, logs)", "jobs").lower()
                files = kernel.storage_manager.list_files(area)
                f_table = Table(title=f"Files in {area}", border_style="blue")
                f_table.add_column("Relative Path")
                f_table.add_column("Size (B)", justify="right")
                f_table.add_column("Modified")
                for f in files:
                    f_table.add_row(f["relative_path"], str(f["size_bytes"]), f["modified"])
                console.print(f_table)
            elif choice == "2":
                path = prompt_text(console, "File path (inside jobs/demo/reports/logs)")
                content = kernel.storage_manager.inspect_file(path)
                console.print(Panel(content or "(empty file)", title="File Preview", border_style="cyan"))
            elif choice == "3":
                path = prompt_text(console, "Temp file path in jobs/ or reports/")
                confirm = prompt_text(console, f"Confirm delete '{path}'? (YES/NO)", "NO").upper()
                if confirm == "YES":
                    deleted = kernel.storage_manager.delete_temp_file(path)
                    console.print(f"[warning]Deleted {deleted}[/warning]")
        except KernelCityError as exc:
            console.print(f"[error]{exc}[/error]")
        pause(console)
