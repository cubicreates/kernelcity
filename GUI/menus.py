from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from GUI.widgets import pause, prompt_int, prompt_text, render_gantt_chart, render_header, run_export_menu
from RES.kernel import KernelEngine
from RES.models import NavigationMode
from RES.PHASE_4_TESTING.error_handling import KernelCityError
from RES.PHASE_5_DEMONSTRATION.demo_datasets import get_demo_memory_scenario
from RES.PHASE_5_DEMONSTRATION.walkthrough import run_complete_walkthrough


def run_city_administration(console: Console, kernel: KernelEngine) -> None:
    while True:
        console.clear()
        cfg = kernel.config_manager.config
        render_header(console, "CITY ADMINISTRATION", "Application Settings & Policies")

        table = Table(border_style="blue")
        table.add_column("Option", style="bold yellow", width=8)
        table.add_column("Setting", style="bold white")
        table.add_column("Current Value", style="cyan")
        table.add_row("1", "Navigation Mode", cfg.navigation_mode)
        table.add_row("2", "CPU Warning Threshold (%)", str(cfg.cpu_warning_threshold))
        table.add_row("3", "RAM Warning Threshold (%)", str(cfg.ram_warning_threshold))
        table.add_row("4", "Disk Warning Threshold (%)", str(cfg.disk_warning_threshold))
        table.add_row("5", "Default Round Robin Quantum", str(cfg.default_time_quantum))
        table.add_row("6", "Job Execution Timeout (s)", str(cfg.job_timeout_seconds))
        table.add_row("7", "Monitor Refresh Interval (s)", str(cfg.monitor_refresh_seconds))
        table.add_row("B", "Return to City Gate", "")
        console.print(table)

        choice = prompt_text(console, "Select option", "B").upper()
        if choice == "B":
            return
        if choice == "1":
            console.print("[info]Modes: 1=EXPLORE, 2=QUICK, 3=SKIP[/info]")
            m = prompt_text(console, "Choose mode (1-3)", "1")
            mapping = {"1": NavigationMode.EXPLORE.value, "2": NavigationMode.QUICK.value, "3": NavigationMode.SKIP.value}
            if m in mapping:
                kernel.config_manager.update(navigation_mode=mapping[m])
                console.print(f"[success]Navigation mode updated to {mapping[m]}.[/success]")
            else:
                console.print("[error]Invalid mode selection.[/error]")
        elif choice == "2":
            val = prompt_int(console, "CPU Warning Threshold (10-100)", int(cfg.cpu_warning_threshold))
            if val is not None and 10 <= val <= 100:
                kernel.config_manager.update(cpu_warning_threshold=float(val))
                kernel.system_monitor.cpu_threshold = float(val)
        elif choice == "3":
            val = prompt_int(console, "RAM Warning Threshold (10-100)", int(cfg.ram_warning_threshold))
            if val is not None and 10 <= val <= 100:
                kernel.config_manager.update(ram_warning_threshold=float(val))
                kernel.system_monitor.ram_threshold = float(val)
        elif choice == "4":
            val = prompt_int(console, "Disk Warning Threshold (10-100)", int(cfg.disk_warning_threshold))
            if val is not None and 10 <= val <= 100:
                kernel.config_manager.update(disk_warning_threshold=float(val))
                kernel.system_monitor.disk_threshold = float(val)
        elif choice == "5":
            val = prompt_int(console, "Default Time Quantum (>=1)", cfg.default_time_quantum)
            if val is not None and val >= 1:
                kernel.config_manager.update(default_time_quantum=val)
        elif choice == "6":
            val = prompt_int(console, "Job Timeout in seconds (>=5)", cfg.job_timeout_seconds)
            if val is not None and val >= 5:
                kernel.config_manager.update(job_timeout_seconds=val)
                kernel.process_manager.default_timeout = val
        elif choice == "7":
            val = prompt_int(console, "Monitor Refresh Interval in seconds (1-30)", int(cfg.monitor_refresh_seconds))
            if val is not None and 1 <= val <= 30:
                kernel.config_manager.update(monitor_refresh_seconds=float(val))
        pause(console)


def run_demo_centre(console: Console, kernel: KernelEngine) -> None:
    while True:
        console.clear()
        render_header(console, "DEMO CENTRE", "Reproducible Demonstrations with Parameter Modification", badge="DEMO")
        table = Table(border_style="cyan")
        table.add_column("Key", style="bold yellow", width=6)
        table.add_column("Demonstration", style="bold white")
        table.add_row("1", "Complete City Walkthrough (All Modules + Report)")
        table.add_row("2", "CPU Scheduling Demonstration (Modifiable Quantum)")
        table.add_row("3", "Memory Allocation Demonstration (Modifiable Requests)")
        table.add_row("4", "Banker's Algorithm Demonstration (Modifiable Request Vector)")
        table.add_row("5", "Deadlock Detection & Recovery Demonstration")
        table.add_row("6", "Live Host Process Monitoring (LIVE)")
        table.add_row("7", "Real Subprocess Job Execution Demonstration")
        table.add_row("8", "Analytics & CSV Export Demonstration")
        table.add_row("B", "Return to City Gate")
        console.print(table)

        choice = prompt_text(console, "Select demonstration", "B").upper()
        if choice == "B":
            return
        try:
            if choice == "1":
                result = run_complete_walkthrough(kernel)
                console.print(Panel(
                    f"[success]Complete City Walkthrough finished![/success]\n"
                    f"Real Jobs Executed: {len(result['real_jobs']['records'])}\n"
                    f"Scheduling Chart: {result['scheduling']['chart_path']}\n"
                    f"Memory Chart: {result['memory']['chart_path']}\n"
                    f"Text Report: {result['text_report']}\n"
                    f"JSON Report: {result['json_report']}",
                    title="Walkthrough Summary",
                    border_style="green",
                ))
            elif choice == "2":
                q = prompt_int(console, "Round Robin Quantum (>=1)", kernel.config_manager.config.default_time_quantum)
                if q is None or q < 1:
                    pause(console)
                    continue
                res = kernel.demo_engine.run_scheduling_demo(quantum=q)
                comp = res["comparison"]
                cmp_table = Table(title=f"DEMO: CPU Scheduling Comparison (Q={q})", border_style="cyan")
                cmp_table.add_column("Algorithm", style="bold white")
                cmp_table.add_column("Avg Waiting", justify="right")
                cmp_table.add_column("Avg Turnaround", justify="right")
                cmp_table.add_column("Avg Response", justify="right")
                cmp_table.add_column("Throughput", justify="right")
                for algo, rep in comp["reports"].items():
                    cmp_table.add_row(algo, f"{rep.avg_waiting_time:.3f}", f"{rep.avg_turnaround_time:.3f}", f"{rep.avg_response_time:.3f}", f"{rep.throughput:.4f}")
                console.print(cmp_table)
                render_gantt_chart(console, comp["reports"]["ROUND_ROBIN"].gantt_chart)
                for obs in comp["observations"]:
                    console.print(f"[info]- {obs}[/info]")
                run_export_menu(
                    console,
                    "demo_scheduling_comparison",
                    kernel.config_manager.reports_dir,
                    csv_fn=lambda fn, od, ov: kernel.analytics.export_scheduling_comparison_csv(comp, filename=fn, output_dir=od, overwrite=ov),
                    json_fn=lambda fn, od, ov: kernel.analytics.export_json_report(fn, comp, output_dir=od, overwrite=ov, use_timestamp=False),
                    chart_fn=lambda: kernel.analytics.charts.generate_scheduling_comparison_chart(comp["reports"]),
                )
                continue
            elif choice == "3":
                scenario = get_demo_memory_scenario()
                block_sizes = list(scenario["block_sizes"])
                requests = list(scenario["requests"])
                extra = prompt_text(console, "Add/test custom request size in KB? (Enter size or leave blank)", "")
                if extra:
                    size_val = int(extra)
                    if size_val <= 0:
                        raise KernelCityError("Request size must be > 0.")
                    requests.append({"reference": "DEMO-CUSTOM", "size": size_val})
                comp = kernel.analytics.run_memory_analysis(kernel.memory_manager, block_sizes, requests)
                mem_table = Table(title="DEMO: Memory Strategy Comparison", border_style="cyan")
                mem_table.add_column("Strategy", style="bold white")
                mem_table.add_column("Allocated", justify="right")
                mem_table.add_column("Failed", justify="right")
                mem_table.add_column("Internal Frag (KB)", justify="right")
                mem_table.add_column("Free (KB)", justify="right")
                for strat, data in comp["results"].items():
                    m = data["metrics"]
                    mem_table.add_row(strat, str(m["allocations_succeeded"]), str(m["allocations_failed"]), str(m["internal_fragmentation"]), str(m["free_memory"]))
                console.print(mem_table)
                run_export_menu(
                    console,
                    "demo_memory_comparison",
                    kernel.config_manager.reports_dir,
                    csv_fn=lambda fn, od, ov: kernel.analytics.export_memory_comparison_csv(comp, filename=fn, output_dir=od, overwrite=ov),
                    json_fn=lambda fn, od, ov: kernel.analytics.export_json_report(fn, comp, output_dir=od, overwrite=ov, use_timestamp=False),
                    chart_fn=lambda: kernel.analytics.charts.generate_memory_comparison_chart(comp["results"]),
                )
                continue
            elif choice == "4":
                res = kernel.demo_engine.run_banker_demo()
                console.print(f"[info]Initial Safe:[/info] {res['initial_safe']} | Sequence: {' -> '.join(res['initial_sequence'])}")
                console.print(f"[success]Safe Request Test:[/success] {res['safe_request_result']['reason']}")
                console.print(f"[warning]Unsafe Request Test:[/warning] {res['unsafe_request_result']['reason']}")
                test_custom = prompt_text(console, "Test a custom request vector? (Y/N)", "N").upper()
                if test_custom == "Y":
                    p_idx = prompt_int(console, "Process index (0..4)", 4)
                    vec_raw = prompt_text(console, "Request vector (3 comma-separated ints)", "1,0,0")
                    vec = [int(x.strip()) for x in vec_raw.split(",")]
                    if p_idx is not None:
                        custom_res = kernel.resource_manager.request_resources(p_idx, vec)
                        console.print(f"[info]{custom_res['reason']}[/info]")
            elif choice == "5":
                res = kernel.demo_engine.run_deadlock_demo()
                console.print("[info]Resource Allocation Graph Edges:[/info]")
                for edge in res["rag"]["assignment_edges"] + res["rag"]["request_edges"]:
                    console.print(f"  {edge}")
                console.print(f"[error]{res['before_recovery']['summary']}[/error]")
                console.print(f"[success]After terminating P0: {res['recovery']['post_recovery_detection']['summary']}[/success]")
            elif choice == "6":
                res = kernel.demo_engine.run_live_monitoring_demo()
                snap = res["snapshot"]
                console.print(f"[success]LIVE HOST READINGS ({snap['timestamp']}):[/success]")
                console.print(f"CPU: {snap['cpu_percent']}% ({snap['cpu_count_logical']} logical cores) | RAM: {snap['ram_percent']}% | Disk: {snap['disk_percent']}% | Processes: {snap['active_processes']}")
            elif choice == "7":
                res = kernel.demo_engine.run_real_job_demo()
                for rec in res["records"]:
                    console.print(f"[success]{rec.job_id}[/success]: {rec.outcome} | exit={rec.exit_code} | duration={rec.duration}s | output={rec.output_location}")
            elif choice == "8":
                res = kernel.demo_engine.run_scheduling_demo()
                csv_path = kernel.analytics.export_scheduling_comparison_csv(res["comparison"])
                json_path = kernel.analytics.export_json_report("demo_scheduling_analysis", res["comparison"])
                console.print(f"[success]Analytics chart: {res['chart_path']}[/success]")
                console.print(f"[success]CSV export: {csv_path}[/success]")
                console.print(f"[success]JSON report: {json_path}[/success]")
            else:
                console.print("[error]Invalid option.[/error]")
        except (KernelCityError, ValueError) as exc:
            console.print(f"[error]{exc}[/error]")
        pause(console)
