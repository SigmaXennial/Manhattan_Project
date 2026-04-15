from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from genealogy_models import ConsistencyIssue, Hint, TreeData
from report_utils import timestamp_label

TREE_EXPORT_FILE = "Tree_Data.json"
CONSISTENCY_EXPORT_FILE = "Consistency_Data.json"
HINTS_EXPORT_FILE = "Research_Hints_Data.json"
CASE_BUNDLE_FILE = "Case_Bundle.json"
ARTIFACT_PATTERNS = ["*.txt", "*.json", "*.ged", "*.jpg", "*.jpeg", "*.png", "*.pdf"]
EXCLUDED_ARTIFACTS = {CASE_BUNDLE_FILE, "Master_Case_Log.txt"}


def write_json(output_path: str, payload: dict[str, Any]) -> str:
    Path(output_path).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output_path


def read_json(output_path: str) -> dict[str, Any] | None:
    path = Path(output_path)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def base_bundle(input_file: str, scope_name: str) -> dict[str, Any]:
    return {
        "generated_at": timestamp_label(),
        "input_file": input_file,
        "scope": scope_name,
        "sections": {
            "tree": None,
            "consistency": None,
            "hints": None,
        },
        "available_sections": [],
        "artifacts": [],
        "artifact_counts": {},
    }


def ensure_bundle(output_path: str, input_file: str = "", scope_name: str = "") -> dict[str, Any]:
    bundle = read_json(output_path)
    if bundle:
        bundle.setdefault("sections", {"tree": None, "consistency": None, "hints": None})
        bundle.setdefault("available_sections", [])
        bundle.setdefault("artifacts", [])
        bundle.setdefault("artifact_counts", {})
        return bundle
    return base_bundle(input_file, scope_name)


def update_case_bundle(section_name: str, section_payload: dict[str, Any], output_path: str = CASE_BUNDLE_FILE) -> str:
    input_file = section_payload.get("input_file", "")
    scope_name = section_payload.get("scope", "")
    bundle = read_json(output_path)

    if not bundle or bundle.get("input_file") != input_file or bundle.get("scope") != scope_name:
        bundle = base_bundle(input_file, scope_name)
    else:
        bundle.setdefault("artifacts", [])
        bundle.setdefault("artifact_counts", {})

    bundle["generated_at"] = timestamp_label()
    bundle["sections"][section_name] = section_payload
    bundle["available_sections"] = [
        name for name, value in bundle["sections"].items() if value is not None
    ]
    write_json(output_path, bundle)
    refresh_case_bundle_artifacts(input_file, scope_name, output_path)
    return output_path


def infer_text_metadata(path: Path) -> tuple[str, str]:
    scope_name = ""
    input_file = ""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[:40]
    except Exception:
        return scope_name, input_file

    for line in lines:
        if line.startswith("Scope:") and not scope_name:
            scope_name = line.split(":", 1)[1].strip()
        elif line.startswith("Target:") and not scope_name:
            scope_name = line.split(":", 1)[1].strip()
        elif line.startswith("Target name:") and not scope_name:
            scope_name = line.split(":", 1)[1].strip()
        elif line.startswith("Input File:") and not input_file:
            input_file = line.split(":", 1)[1].strip()
        elif line.startswith("Case Folder:") and not input_file:
            input_file = line.split(":", 1)[1].strip()
    return scope_name, input_file


def infer_json_metadata(path: Path) -> tuple[str, str]:
    payload = read_json(str(path))
    if not payload:
        return "", ""
    return str(payload.get("scope", "")), str(payload.get("input_file", ""))


def artifact_type(path: Path) -> str:
    suffix = path.suffix.lower()
    name = path.name.lower()
    if suffix == ".json":
        return "structured_data"
    if suffix == ".ged":
        return "tree_file"
    if suffix in {".jpg", ".jpeg", ".png", ".pdf"}:
        return "document"
    if "recon" in name:
        return "research_report"
    if "transcription" in name:
        return "transcription_report"
    if "index" in name or "locker" in name:
        return "evidence_index"
    if "proof" in name or "draft" in name or "summary" in name:
        return "proof_report"
    return "report"


def gather_artifact_paths() -> list[Path]:
    artifacts: dict[str, Path] = {}
    for pattern in ARTIFACT_PATTERNS:
        for path in Path(".").glob(pattern):
            if path.is_file() and path.parent == Path(".") and path.name not in EXCLUDED_ARTIFACTS:
                artifacts[str(path)] = path
    return [artifacts[key] for key in sorted(artifacts.keys())]


def artifact_entry(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".json":
        scope_name, input_file = infer_json_metadata(path)
    else:
        scope_name, input_file = infer_text_metadata(path)

    stat = path.stat()
    return {
        "file_name": path.name,
        "relative_path": str(path),
        "artifact_type": artifact_type(path),
        "scope": scope_name,
        "input_file": input_file,
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
    }


def refresh_case_bundle_artifacts(input_file: str = "", scope_name: str = "", output_path: str = CASE_BUNDLE_FILE) -> str:
    bundle = ensure_bundle(output_path, input_file, scope_name)
    if input_file and not bundle.get("input_file"):
        bundle["input_file"] = input_file
    if scope_name and not bundle.get("scope"):
        bundle["scope"] = scope_name

    artifacts = [artifact_entry(path) for path in gather_artifact_paths()]
    bundle["generated_at"] = timestamp_label()
    bundle["artifacts"] = artifacts
    bundle["artifact_counts"] = dict(Counter(entry["artifact_type"] for entry in artifacts))
    return write_json(output_path, bundle)


def tree_payload(
    tree: TreeData,
    person_ids: list[str],
    family_ids: list[str],
    scope_name: str,
    lineage_narrative: str,
) -> dict[str, Any]:
    scoped_source_ids = {
        ref.id
        for person_id in person_ids
        for ref in tree.persons[person_id].source_refs
        if ref.id
    }
    scoped_source_ids.update(
        ref.id
        for family_id in family_ids
        for ref in tree.families[family_id].source_refs
        if ref.id
    )

    return {
        "generated_at": timestamp_label(),
        "input_file": tree.gedcom_file,
        "scope": scope_name,
        "counts": {
            "total_people": len(tree.persons),
            "total_families": len(tree.families),
            "total_sources": len(tree.sources),
            "people_in_scope": len(person_ids),
            "families_in_scope": len(family_ids),
        },
        "people": [asdict(tree.persons[person_id]) for person_id in person_ids],
        "families": [asdict(tree.families[family_id]) for family_id in family_ids],
        "sources": [asdict(tree.sources[source_id]) for source_id in sorted(scoped_source_ids) if source_id in tree.sources],
        "lineage_narrative": lineage_narrative,
    }


def export_tree_json(
    tree: TreeData,
    person_ids: list[str],
    family_ids: list[str],
    scope_name: str,
    lineage_narrative: str,
    output_path: str = TREE_EXPORT_FILE,
    bundle_path: str = CASE_BUNDLE_FILE,
) -> str:
    payload = tree_payload(tree, person_ids, family_ids, scope_name, lineage_narrative)
    write_json(output_path, payload)
    update_case_bundle("tree", payload, bundle_path)
    return output_path


def consistency_payload(
    gedcom_path: str,
    scope_name: str,
    person_ids: list[str],
    family_ids: list[str],
    issues: list[ConsistencyIssue],
) -> dict[str, Any]:
    return {
        "generated_at": timestamp_label(),
        "input_file": gedcom_path,
        "scope": scope_name,
        "counts": {
            "people_reviewed": len(person_ids),
            "families_reviewed": len(family_ids),
            "issues_found": len(issues),
        },
        "issues": [asdict(issue) for issue in issues],
    }


def export_consistency_json(
    gedcom_path: str,
    scope_name: str,
    person_ids: list[str],
    family_ids: list[str],
    issues: list[ConsistencyIssue],
    output_path: str = CONSISTENCY_EXPORT_FILE,
    bundle_path: str = CASE_BUNDLE_FILE,
) -> str:
    payload = consistency_payload(gedcom_path, scope_name, person_ids, family_ids, issues)
    write_json(output_path, payload)
    update_case_bundle("consistency", payload, bundle_path)
    return output_path


def hints_payload(
    gedcom_path: str,
    scope_name: str,
    person_ids: list[str],
    family_ids: list[str],
    hints: list[Hint],
) -> dict[str, Any]:
    return {
        "generated_at": timestamp_label(),
        "input_file": gedcom_path,
        "scope": scope_name,
        "counts": {
            "people_reviewed": len(person_ids),
            "families_reviewed": len(family_ids),
            "hints_generated": len(hints),
        },
        "hints": [asdict(hint) for hint in hints],
    }


def export_hints_json(
    gedcom_path: str,
    scope_name: str,
    person_ids: list[str],
    family_ids: list[str],
    hints: list[Hint],
    output_path: str = HINTS_EXPORT_FILE,
    bundle_path: str = CASE_BUNDLE_FILE,
) -> str:
    payload = hints_payload(gedcom_path, scope_name, person_ids, family_ids, hints)
    write_json(output_path, payload)
    update_case_bundle("hints", payload, bundle_path)
    return output_path
