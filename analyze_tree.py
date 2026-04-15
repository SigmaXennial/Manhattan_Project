from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from gedcom_parser import parse_gedcom, resolve_scope
from genealogy_models import Event, Family, Person, TreeData
from json_export import export_tree_json
from report_utils import write_report

REPORT_FILE = "Tree_Structure_Report.txt"
JSON_FILE = "Tree_Data.json"


def format_event(event: Event | None) -> str:
    if event is None:
        return "Unknown"
    parts = []
    if event.date:
        parts.append(event.date)
    if event.place:
        parts.append(event.place)
    if not parts:
        return "Unknown"
    return " | ".join(parts)


def person_block(person: Person) -> str:
    birth = format_event(person.get_event("BIRT"))
    death = format_event(person.get_event("DEAT"))
    residences = [format_event(event) for event in person.events if event.type == "RESI"]
    residence_text = "; ".join(residences[:3]) if residences else "None recorded"
    source_ids = ", ".join(sorted({ref.id for ref in person.source_refs if ref.id})) or "None listed"
    return "\n".join(
        [
            f"{person.primary_name} ({person.id})",
            f"Sex: {person.sex or 'Unknown'}",
            f"Birth: {birth}",
            f"Death: {death}",
            f"Child in family: {person.family_as_child or 'Unknown'}",
            f"Spouse families: {', '.join(person.families_as_spouse) or 'None'}",
            f"Recent residences: {residence_text}",
            f"Source references: {source_ids}",
        ]
    )


def family_block(tree: TreeData, family: Family) -> str:
    husband = tree.persons.get(family.husband_id)
    wife = tree.persons.get(family.wife_id)
    marriage = format_event(family.get_event("MARR"))
    children = [tree.persons[child_id].primary_name for child_id in family.child_ids if child_id in tree.persons]
    source_ids = ", ".join(sorted({ref.id for ref in family.source_refs if ref.id})) or "None listed"
    return "\n".join(
        [
            f"Family {family.id}",
            f"Spouses: {(husband.primary_name if husband else 'Unknown')} / {(wife.primary_name if wife else 'Unknown')}",
            f"Marriage: {marriage}",
            f"Children: {', '.join(children) if children else 'None recorded'}",
            f"Source references: {source_ids}",
        ]
    )


def family_summary_for_prompt(tree: TreeData, family: Family) -> str:
    husband = tree.persons.get(family.husband_id)
    wife = tree.persons.get(family.wife_id)
    children = [tree.persons[child_id].primary_name for child_id in family.child_ids if child_id in tree.persons]
    return "\n".join(
        [
            f"Family ID: {family.id}",
            f"Husband: {husband.primary_name if husband else 'Unknown'} ({format_event(husband.get_event('BIRT')) if husband else 'Unknown'} - {format_event(husband.get_event('DEAT')) if husband else 'Unknown'})",
            f"Wife: {wife.primary_name if wife else 'Unknown'} ({format_event(wife.get_event('BIRT')) if wife else 'Unknown'} - {format_event(wife.get_event('DEAT')) if wife else 'Unknown'})",
            f"Marriage: {format_event(family.get_event('MARR'))}",
            f"Children: {', '.join(children) if children else 'None recorded'}",
        ]
    )


def generate_lineage_narrative(tree: TreeData, family_ids: list[str], scope_name: str) -> str:
    selected_families = [tree.families[family_id] for family_id in family_ids[:12]]
    if not selected_families:
        return "No family scope was available for narrative generation."

    prompt_input = "\n\n".join(family_summary_for_prompt(tree, family) for family in selected_families)
    prompt = ChatPromptTemplate.from_template(
        """
You are an expert genealogist preparing a concise lineage briefing.
Summarize the relationships, chronology, and notable evidence gaps for the following family summaries.
Keep the writing factual and hypothesis-aware. Do not invent facts. Make it clear that uncertain points need record review.

Scope: {scope_name}

Family summaries:
{family_summaries}
"""
    )

    try:
        llm = ChatOllama(model="dolphin-mixtral", temperature=0.1)
        chain = prompt | llm | StrOutputParser()
        return chain.invoke({"scope_name": scope_name, "family_summaries": prompt_input}).strip()
    except Exception as exc:
        return f"AI lineage narrative unavailable: {exc}"


def run_tree_analysis(gedcom_path: str, target_scope: str | None = None) -> str:
    tree = parse_gedcom(gedcom_path)
    person_ids, family_ids, scope_name = resolve_scope(tree, target_scope)

    people_text = "\n\n".join(person_block(tree.persons[person_id]) for person_id in person_ids)
    families_text = "\n\n".join(family_block(tree, tree.families[family_id]) for family_id in family_ids)
    narrative = generate_lineage_narrative(tree, family_ids, scope_name)
    source_ids = sorted(
        {
            ref.id
            for person_id in person_ids
            for ref in tree.persons[person_id].source_refs
            if ref.id
        }
        | {
            ref.id
            for family_id in family_ids
            for ref in tree.families[family_id].source_refs
            if ref.id
        }
    )

    sections = [
        (
            "Tree Overview",
            "\n".join(
                [
                    f"Total people in file: {len(tree.persons)}",
                    f"Total families in file: {len(tree.families)}",
                    f"People in scope: {len(person_ids)}",
                    f"Families in scope: {len(family_ids)}",
                    f"Cataloged sources: {len(tree.sources)}",
                    f"JSON export: {JSON_FILE}",
                ]
            ),
        ),
        ("Structured People", people_text),
        ("Structured Families", families_text),
        ("AI Lineage Narrative", narrative),
    ]

    write_report(
        REPORT_FILE,
        "Tree Structure Report",
        gedcom_path,
        scope_name,
        sections,
        source_list=source_ids,
        confidence_notes=[
            "Structured People and Structured Families are deterministic GEDCOM extractions.",
            "The AI narrative is a researcher aid and should be treated as a summary, not authority.",
            "The JSON export is a local structured cache intended for Phase 2-ready reuse.",
        ],
        next_steps=[
            "Run the consistency checker to surface chronology and relationship anomalies.",
            "Run the research hint engine to identify missing records and archive targets.",
        ],
    )
    export_tree_json(tree, person_ids, family_ids, scope_name, narrative, JSON_FILE)
    return REPORT_FILE


def main() -> None:
    gedcom_path = input("GEDCOM file path [bissell.ged]: ").strip() or "bissell.ged"
    target_scope = input("Target person or family (optional): ").strip() or None
    output = run_tree_analysis(gedcom_path, target_scope)
    print(f"\n[+] Tree analysis complete. Report written to {output}")
    print(f"[+] Structured JSON export written to {JSON_FILE}")


if __name__ == "__main__":
    main()
