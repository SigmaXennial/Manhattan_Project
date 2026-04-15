from __future__ import annotations

import re
import shutil
from pathlib import Path

BASE_DIR = Path("Evidence_Locker")


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip())
    return cleaned.strip("_") or "General_Research"


def categorize(path: Path) -> str:
    name = path.name.lower()
    if path.suffix.lower() == ".ged":
        return "Tree_Files"
    if "transcription" in name:
        return "Transcriptions"
    if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".pdf"}:
        return "Documents"
    if "recon" in name:
        return "Research"
    return "Reports"


def infer_scope_from_report(path: Path) -> str:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[:25]
    except Exception:
        return "Unspecified"

    for line in lines:
        if line.startswith("Scope:"):
            return line.split(":", 1)[1].strip() or "Unspecified"
        if line.startswith("Target:"):
            return line.split(":", 1)[1].strip() or "Unspecified"
        if line.startswith("Target name:"):
            return line.split(":", 1)[1].strip() or "Unspecified"
    return "Unspecified"


def gather_artifacts() -> list[Path]:
    patterns = ["*.txt", "*.ged", "*.jpg", "*.jpeg", "*.png", "*.pdf"]
    artifacts: dict[str, Path] = {}
    for pattern in patterns:
        for path in Path(".").glob(pattern):
            if path.is_file() and path.parent == Path("."):
                artifacts[str(path)] = path
    return [artifacts[key] for key in sorted(artifacts.keys())]


def organize_evidence(case_name: str | None = None) -> str:
    case_folder = BASE_DIR / slugify(case_name or "General Research")
    case_folder.mkdir(parents=True, exist_ok=True)

    index_lines = [
        "Evidence Index",
        "==============",
        f"Case Folder: {case_folder}",
        "",
    ]

    for artifact in gather_artifacts():
        if artifact.name == "Evidence_Index.txt":
            continue
        category = categorize(artifact)
        destination_dir = case_folder / category
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / artifact.name
        shutil.copy2(artifact, destination)
        inferred_scope = infer_scope_from_report(artifact) if artifact.suffix.lower() == ".txt" else "Unspecified"
        index_lines.extend(
            [
                f"Artifact: {artifact.name}",
                f"Category: {category}",
                f"Scope / Target: {inferred_scope}",
                f"Archived Copy: {destination}",
                "",
            ]
        )

    Path("Evidence_Index.txt").write_text("\n".join(index_lines).strip() + "\n", encoding="utf-8")
    print(f"\n[+] Evidence locker refreshed. Index written to Evidence_Index.txt")
    return "Evidence_Index.txt"


def main() -> None:
    case_name = input("Case name (optional): ").strip() or None
    organize_evidence(case_name)


if __name__ == "__main__":
    main()
