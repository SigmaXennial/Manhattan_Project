from __future__ import annotations

from pathlib import Path

SCRIPTS = [
    "bot.py",
    "analyze_tree.py",
    "gedcom_parser.py",
    "genealogy_models.py",
    "json_export.py",
    "consistency_checker.py",
    "hint_engine.py",
    "external_recon.py",
    "master_investigator.py",
    "transcribe_doc.py",
    "compiler.py",
    "evidence_locker.py",
    "report_utils.py",
]

DATA_FILES = [
    "bissell.ged",
]

OPTIONAL_IMAGE_TARGETS = [
    "document.jpg",
    "document_Page_1.jpg",
    "document_Page_4.jpg",
    "document_Page_5.jpg",
    "document_Page_6.jpg",
    "document_Page_7.jpg",
]

OPTIONAL_JSON_EXPORTS = [
    "Tree_Data.json",
    "Consistency_Data.json",
    "Research_Hints_Data.json",
    "Case_Bundle.json",
]


def check_system() -> None:
    print("\n--- Genealogy Intelligence Platform: System Health Check ---")
    print("Scanning local environment for core workflows and source files...\n")

    missing = []

    print("[*] Checking workflow scripts:")
    for script in SCRIPTS:
        if Path(script).exists():
            print(f"  [OK]  {script}")
        else:
            print(f"  [!!]  MISSING: {script}")
            missing.append(script)

    print("\n[*] Checking GEDCOM / primary data files:")
    for data_file in DATA_FILES:
        if Path(data_file).exists():
            print(f"  [OK]  {data_file}")
        else:
            print(f"  [!!]  MISSING: {data_file}")
            missing.append(data_file)

    print("\n[*] Checking document intelligence inputs:")
    available_images = [path for path in OPTIONAL_IMAGE_TARGETS if Path(path).exists()]
    if available_images:
        for image_path in available_images:
            print(f"  [OK]  {image_path}")
    else:
        print("  [!!]  No transcription-ready document images were found.")

    print("\n[*] Checking optional structured exports:")
    available_exports = [path for path in OPTIONAL_JSON_EXPORTS if Path(path).exists()]
    if available_exports:
        for export_path in available_exports:
            print(f"  [OK]  {export_path}")
    else:
        print("  [--]  No JSON exports generated yet.")

    if not missing:
        print("\n[+] SYSTEM READY: Core genealogy workflows are present.")
    else:
        print(f"\n[-] SYSTEM INCOMPLETE: {len(missing)} required assets are missing.")


if __name__ == "__main__":
    check_system()
