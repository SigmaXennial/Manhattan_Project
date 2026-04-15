from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from genealogy_models import ConsistencyIssue, Hint, TreeData
from report_utils import timestamp_label

TREE_EXPORT_FILE = "Tree_Data.json"
CONSISTENCY_EXPORT_FILE = "Consistency_Data.json"
HINTS_EXPORT_FILE = "Research_Hints_Data.json"
CASE_BUNDLE_FILE = "Case_Bundle.json"


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
    }


def update_case_bundle(section_name: str, section_payload: dict[str, Any], output_path: str = CASE_BUNDLE_FILE) -> str:
    input_file = section_payload.get("input_file", "")
    scope_name = section_payload.get("scope", "")
    bundle = read_json(output_path)

    if not bundle or bundle.get("input_file") != input_file or bundle.get("scope") != scope_name:
        bundle = base_bundle(input_file, scope_name)

    bundle["generated_at"] = timestamp_label()
    bundle["sections"][section_name] = section_payload
    bundle["available_sections"] = [
        name for name, value in bundle["sections"].items() if value is not None
    ]
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
