from __future__ import annotations

import json
import re
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
DEFAULT_CASE_OUTPUTS = {
    "Tree_Structure_Report.txt",
    "Consistency_Report.txt",
    "Research_Hints_Report.txt",
    "External_Recon_Report.txt",
    "Broad_Web_Recon_Report.txt",
    "Transcription_Report.txt",
    "Evidence_Index.txt",
    "Proof_Summary_Draft.txt",
    TREE_EXPORT_FILE,
    CONSISTENCY_EXPORT_FILE,
    HINTS_EXPORT_FILE,
}


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
        "person_artifacts": [],
        "person_artifact_counts": {},
    }


def ensure_bundle(output_path: str, input_file: str = "", scope_name: str = "") -> dict[str, Any]:
    bundle = read_json(output_path)
    if bundle:
        bundle.setdefault("sections", {"tree": None, "consistency": None, "hints": None})
        bundle.setdefault("available_sections", [])
        bundle.setdefault("artifacts", [])
        bundle.setdefault("artifact_counts", {})
        bundle.setdefault("person_artifacts", [])
        bundle.setdefault("person_artifact_counts", {})
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
        bundle.setdefault("person_artifacts", [])
        bundle.setdefault("person_artifact_counts", {})

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


def normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def unique_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        clean_value = value.strip()
        if clean_value and clean_value not in seen:
            seen.add(clean_value)
            ordered.append(clean_value)
    return ordered


def person_name_candidates(person_payload: dict[str, Any]) -> list[str]:
    names = [str(person_payload.get("primary_name", ""))]
    given_name = str(person_payload.get("given_name", "")).strip()
    surname = str(person_payload.get("surname", "")).strip()
    combined_name = " ".join(part for part in [given_name, surname] if part).strip()
    if combined_name:
        names.append(combined_name)
    names.extend(str(name) for name in person_payload.get("name_variants", []) if str(name).strip())
    return unique_strings(names)


def file_reference(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "file_name": entry.get("file_name", ""),
        "relative_path": entry.get("relative_path", ""),
        "artifact_type": entry.get("artifact_type", "report"),
    }


def artifact_matches_bundle(entry: dict[str, Any], bundle: dict[str, Any]) -> bool:
    bundle_input = str(bundle.get("input_file", "")).strip()
    bundle_scope = normalize_text(str(bundle.get("scope", "")))
    artifact_input = str(entry.get("input_file", "")).strip()
    artifact_scope = normalize_text(str(entry.get("scope", "")))
    file_name = str(entry.get("file_name", ""))

    if file_name in DEFAULT_CASE_OUTPUTS:
        return True
    if bundle_input and artifact_input == bundle_input:
        return True
    if bundle_scope and artifact_scope and artifact_scope == bundle_scope:
        return True
    return False


def artifact_matches_person(entry: dict[str, Any], person_payload: dict[str, Any]) -> bool:
    artifact_scope = normalize_text(str(entry.get("scope", "")))
    artifact_input = normalize_text(str(entry.get("input_file", "")))
    if not artifact_scope and not artifact_input:
        return False

    person_id = str(person_payload.get("id", "")).strip()
    normalized_person_id = normalize_text(person_id)
    names = [normalize_text(name) for name in person_name_candidates(person_payload)]
    haystacks = [value for value in [artifact_scope, artifact_input] if value]

    for haystack in haystacks:
        if normalized_person_id and haystack == normalized_person_id:
            return True
        for name in names:
            if not name or len(name) < 4:
                continue
            if haystack == name or name in haystack:
                return True
    return False


def person_matches_scope(person_payload: dict[str, Any], scope_name: str) -> bool:
    normalized_scope = normalize_text(scope_name)
    if not normalized_scope or normalized_scope == "entire tree":
        return False

    person_id = normalize_text(str(person_payload.get("id", "")))
    if person_id and normalized_scope == person_id:
        return True

    for name in person_name_candidates(person_payload):
        normalized_name = normalize_text(name)
        if not normalized_name or len(normalized_name) < 4:
            continue
        if normalized_scope == normalized_name or normalized_name in normalized_scope or normalized_scope in normalized_name:
            return True
    return False


def issue_reference(issue: dict[str, Any]) -> dict[str, Any]:
    return {
        "issue_type": issue.get("issue_type", ""),
        "severity": issue.get("severity", "medium"),
        "affected_ids": issue.get("affected_ids", []),
    }


def hint_reference(hint: dict[str, Any]) -> dict[str, Any]:
    return {
        "target_id": hint.get("target_id", ""),
        "target_name": hint.get("target_name", ""),
        "hint_type": hint.get("hint_type", ""),
        "confidence": hint.get("confidence", "medium"),
    }


def build_person_artifact_mapping(bundle: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    tree_section = bundle.get("sections", {}).get("tree") or {}
    people = tree_section.get("people", [])
    if not people:
        return [], {
            "people_mapped": 0,
            "people_with_direct_artifacts": 0,
            "people_with_issue_refs": 0,
            "people_with_hint_refs": 0,
        }

    consistency_section = bundle.get("sections", {}).get("consistency") or {}
    hints_section = bundle.get("sections", {}).get("hints") or {}
    issues = consistency_section.get("issues", [])
    hints = hints_section.get("hints", [])
    artifacts = bundle.get("artifacts", [])
    relevant_artifacts = [entry for entry in artifacts if artifact_matches_bundle(entry, bundle)] or artifacts
    case_artifact_refs = [file_reference(entry) for entry in relevant_artifacts]

    person_entries: list[dict[str, Any]] = []
    people_with_direct_artifacts = 0
    people_with_issue_refs = 0
    people_with_hint_refs = 0

    for person in people:
        person_id = str(person.get("id", ""))
        family_ids = {
            str(person.get("family_as_child", "")).strip(),
            *(str(family_id).strip() for family_id in person.get("families_as_spouse", [])),
        }
        family_ids.discard("")

        direct_artifact_refs = [
            file_reference(entry)
            for entry in relevant_artifacts
            if artifact_matches_person(entry, person)
        ]
        related_issue_refs = [
            issue_reference(issue)
            for issue in issues
            if person_id in issue.get("affected_ids", []) or family_ids.intersection(issue.get("affected_ids", []))
        ]
        related_hint_refs = [
            hint_reference(hint)
            for hint in hints
            if hint.get("target_id") == person_id or hint.get("target_id") in family_ids
        ]

        if direct_artifact_refs:
            people_with_direct_artifacts += 1
        if related_issue_refs:
            people_with_issue_refs += 1
        if related_hint_refs:
            people_with_hint_refs += 1

        person_entries.append(
            {
                "person_id": person_id,
                "person_name": person.get("primary_name", "Unknown"),
                "name_variants": person_name_candidates(person),
                "is_primary_scope_match": person_matches_scope(person, str(bundle.get("scope", ""))),
                "case_artifact_refs": case_artifact_refs,
                "direct_artifact_refs": direct_artifact_refs,
                "related_issue_refs": related_issue_refs,
                "related_hint_refs": related_hint_refs,
            }
        )

    counts = {
        "people_mapped": len(person_entries),
        "people_with_direct_artifacts": people_with_direct_artifacts,
        "people_with_issue_refs": people_with_issue_refs,
        "people_with_hint_refs": people_with_hint_refs,
    }
    return person_entries, counts


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
    person_artifacts, person_artifact_counts = build_person_artifact_mapping(bundle)
    bundle["person_artifacts"] = person_artifacts
    bundle["person_artifact_counts"] = person_artifact_counts
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
