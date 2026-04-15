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


def write_json(output_path: str, payload: dict[str, Any]) -> str:
    Path(output_path).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output_path


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
) -> str:
    return write_json(output_path, tree_payload(tree, person_ids, family_ids, scope_name, lineage_narrative))


def export_consistency_json(
    gedcom_path: str,
    scope_name: str,
    person_ids: list[str],
    family_ids: list[str],
    issues: list[ConsistencyIssue],
    output_path: str = CONSISTENCY_EXPORT_FILE,
) -> str:
    payload = {
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
    return write_json(output_path, payload)


def export_hints_json(
    gedcom_path: str,
    scope_name: str,
    person_ids: list[str],
    family_ids: list[str],
    hints: list[Hint],
    output_path: str = HINTS_EXPORT_FILE,
) -> str:
    payload = {
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
    return write_json(output_path, payload)
