from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

from analyze_tree import run_tree_analysis
from compiler import compile_proof_summary
from consistency_checker import run_consistency_check
from evidence_locker import organize_evidence
from external_recon import run_external_recon
from hint_engine import run_hint_generation
from inventory import check_system
from master_investigator import get_research_parameters, run_broad_recon
from transcribe_doc import transcribe_document

LOG_FILE = "Master_Case_Log.txt"


def log_event(event_name: str, details: str = "No additional details provided.") -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] WORKFLOW: {event_name}\n")
        log_file.write(f"DETAILS: {details}\n")
        log_file.write("-" * 60 + "\n")


def clear_screen() -> None:
    command = "cls" if sys.platform == "win32" else "clear"
    os.system(command)


def pause() -> None:
    input("\nPress Enter to return to the console...")


def prompt_tree_scope(current_gedcom: str, current_target: str) -> tuple[str, str | None]:
    gedcom_path = input(f"GEDCOM file path [{current_gedcom}]: ").strip() or current_gedcom
    prompt = f"Target person or family [{current_target or 'entire tree'}] (type 'all' for entire tree): "
    target_scope = input(prompt).strip()
    if target_scope.lower() == "all":
        return gedcom_path, None
    if not target_scope:
        target_scope = current_target or None
    return gedcom_path, target_scope


def view_log() -> None:
    path = Path(LOG_FILE)
    if not path.exists():
        print("\n[-] No log file exists yet.")
        return
    print(f"\n--- {LOG_FILE} ---\n")
    print(path.read_text(encoding="utf-8", errors="replace")[-5000:])


def run_guided_workflow(current_gedcom: str, current_target: str) -> tuple[str, str | None]:
    gedcom_path, target_scope = prompt_tree_scope(current_gedcom, current_target)
    log_event("GUIDED WORKFLOW", f"GEDCOM={gedcom_path}; Scope={target_scope or 'Entire tree'}")

    print("\n[1/4] Building tree structure report...")
    run_tree_analysis(gedcom_path, target_scope)
    print("[2/4] Running consistency review...")
    run_consistency_check(gedcom_path, target_scope)
    print("[3/4] Generating research hints...")
    _, hints = run_hint_generation(gedcom_path, target_scope)

    if hints:
        run_archival = input("Run external archival search for the same scope now? [y/N]: ").strip().lower()
        if run_archival == "y":
            run_external_recon(target_name=target_scope or hints[0].target_name, target_scope=target_scope or hints[0].target_name)

    compile_now = input("Compile a proof summary draft now? [y/N]: ").strip().lower()
    if compile_now == "y":
        print("[4/4] Compiling proof summary draft...")
        compile_proof_summary()

    return gedcom_path, target_scope


def main_menu() -> None:
    current_gedcom = "bissell.ged"
    current_target = ""

    while True:
        clear_screen()
        print("=== Genealogy Intelligence Platform: Operations Console ===")
        print(f"Active GEDCOM: {current_gedcom}")
        print(f"Active Scope: {current_target or 'Entire tree'}")
        print(f"Log File: {LOG_FILE}")
        print("-" * 60)
        print("Tree Intake")
        print("  1. Import / parse GEDCOM and build tree structure report")
        print("  2. Run consistency checker")
        print("  3. Generate research hints")
        print("Research Assistance")
        print("  4. Run external archival search")
        print("  5. Run broad web recon")
        print("Document Intelligence")
        print("  6. Transcribe historical document")
        print("Case Assembly")
        print("  7. Compile proof summary draft")
        print("  8. Organize evidence locker")
        print("Workflow")
        print("  9. Guided workflow: parse → check → hint → compile")
        print("System")
        print(" 10. View logs")
        print(" 11. Health check")
        print(" 12. Exit")
        print("-" * 60)

        choice = input("Select workflow (1-12): ").strip()

        if choice == "1":
            current_gedcom, current_target = prompt_tree_scope(current_gedcom, current_target)
            log_event("TREE ANALYSIS", f"GEDCOM={current_gedcom}; Scope={current_target or 'Entire tree'}")
            run_tree_analysis(current_gedcom, current_target)
            pause()
        elif choice == "2":
            current_gedcom, current_target = prompt_tree_scope(current_gedcom, current_target)
            log_event("CONSISTENCY CHECK", f"GEDCOM={current_gedcom}; Scope={current_target or 'Entire tree'}")
            run_consistency_check(current_gedcom, current_target)
            pause()
        elif choice == "3":
            current_gedcom, current_target = prompt_tree_scope(current_gedcom, current_target)
            log_event("RESEARCH HINTS", f"GEDCOM={current_gedcom}; Scope={current_target or 'Entire tree'}")
            run_hint_generation(current_gedcom, current_target)
            pause()
        elif choice == "4":
            target_name = input(f"Target name [{current_target or ''}]: ").strip() or current_target
            if not target_name:
                print("\n[-] A target name is required for archival search.")
            else:
                birth_year = input("Birth year (optional): ").strip()
                death_year = input("Death year (optional): ").strip()
                place = input("Place (optional): ").strip()
                record_focus = input("Record focus (optional): ").strip()
                log_event("EXTERNAL RECON", f"Target={target_name}; Place={place or 'N/A'}; Focus={record_focus or 'General'}")
                run_external_recon(target_name, birth_year, death_year, place, record_focus, target_name)
            pause()
        elif choice == "5":
            try:
                params = get_research_parameters()
            except ValueError as exc:
                print(f"\n[-] {exc}")
            else:
                log_event("BROAD WEB RECON", f"Target={params['name']}")
                run_broad_recon(params)
            pause()
        elif choice == "6":
            image_path = input("Image file path [document.jpg]: ").strip() or "document.jpg"
            log_event("TRANSCRIPTION", f"Image={image_path}")
            transcribe_document(image_path)
            pause()
        elif choice == "7":
            log_event("PROOF SUMMARY", "Compiled proof summary draft from available reports.")
            compile_proof_summary()
            pause()
        elif choice == "8":
            case_name = input("Case name (optional): ").strip() or current_target or None
            log_event("EVIDENCE LOCKER", f"Case={case_name or 'General Research'}")
            organize_evidence(case_name)
            pause()
        elif choice == "9":
            current_gedcom, current_target = run_guided_workflow(current_gedcom, current_target)
            pause()
        elif choice == "10":
            view_log()
            pause()
        elif choice == "11":
            check_system()
            pause()
        elif choice == "12":
            log_event("SHUTDOWN", "Operator closed the genealogy operations console.")
            print("\n[+] Powering down.")
            break
        else:
            print("\n[-] Invalid selection.")
            pause()


if __name__ == "__main__":
    main_menu()
