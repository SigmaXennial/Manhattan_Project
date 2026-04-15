from __future__ import annotations

from collections import Counter

from gedcom_parser import parse_gedcom, resolve_scope
from genealogy_models import Event, Hint, Person, TreeData
from report_utils import write_report

REPORT_FILE = "Research_Hints_Report.txt"


def extract_year(date_text: str) -> int | None:
    digits = [token for token in date_text.replace("/", " ").replace("-", " ").split() if token.isdigit() and len(token) == 4]
    if digits:
        return int(digits[0])
    return None


def first_place(event: Event | None) -> str:
    return event.place if event and event.place else ""


def build_hint(
    person: Person,
    hint_type: str,
    rationale: str,
    record_types: list[str],
    queries: list[str],
    repositories: list[str],
    confidence: str,
    unresolved_questions: list[str],
) -> Hint:
    return Hint(
        target_id=person.id,
        target_name=person.primary_name,
        hint_type=hint_type,
        rationale=rationale,
        suggested_record_types=record_types,
        search_queries=queries,
        repositories=repositories,
        confidence=confidence,
        unresolved_questions=unresolved_questions,
    )


def person_birth(person: Person) -> Event | None:
    return person.get_event("BIRT")


def person_death(person: Person) -> Event | None:
    return person.get_event("DEAT")


def birth_year(person: Person) -> int | None:
    birth = person_birth(person)
    return extract_year(birth.date) if birth else None


def death_year(person: Person) -> int | None:
    death = person_death(person)
    return extract_year(death.date) if death else None


def person_location(person: Person) -> str:
    for tag in ["BIRT", "RESI", "DEAT"]:
        event = person.get_event(tag)
        if event and event.place:
            return event.place
    return ""


def repositories_for_place(place: str) -> list[str]:
    suggestions = ["FamilySearch Catalog", "Local county clerk or archives"]
    if "ohio" in place.lower():
        suggestions.insert(0, "Ohio History Connection")
    if "new york" in place.lower() or "ny" in place.lower():
        suggestions.insert(0, "New York State Archives")
    if "pennsylvania" in place.lower():
        suggestions.insert(0, "Pennsylvania State Archives")
    if "massachusetts" in place.lower() or "connecticut" in place.lower():
        suggestions.insert(0, "New England Historic Genealogical Society")
    return suggestions[:3]


def build_person_hints(person: Person) -> list[Hint]:
    hints: list[Hint] = []
    birth = person_birth(person)
    death = person_death(person)
    birth_place = first_place(birth)
    death_place = first_place(death)
    known_place = birth_place or person_location(person)
    born_year = birth_year(person)
    died_year = death_year(person)

    if birth is None or not birth.date or not birth.place:
        query = person.primary_name
        if known_place:
            query = f"{query} {known_place}"
        hints.append(
            build_hint(
                person,
                "Missing birth evidence",
                "The tree lacks a complete birth event with both date and place.",
                ["Birth certificate", "Church baptism register", "Town birth register"],
                [query, f"{person.primary_name} baptism"],
                repositories_for_place(known_place or "") or ["FamilySearch Catalog"],
                "high",
                ["What is the exact birth date and place?", "Which record provides the earliest direct birth evidence?"],
            )
        )

    if death is None or not death.date:
        query = person.primary_name
        if known_place:
            query = f"{query} obituary {known_place}"
        hints.append(
            build_hint(
                person,
                "Missing death evidence",
                "The profile does not contain a complete death event.",
                ["Death certificate", "Obituary", "Burial record", "Probate file"],
                [query, f"{person.primary_name} probate"],
                repositories_for_place(death_place or known_place or "") + ["Find A Grave"],
                "high",
                ["When and where did this person die?", "Is there a probate or burial record that confirms the death?"],
            )
        )

    if born_year and born_year <= 1940:
        latest_year = died_year or min(born_year + 80, 1950)
        census_years = [year for year in range(((born_year // 10) + 1) * 10, min(latest_year, 1950) + 1, 10)]
        if census_years:
            place_text = known_place or "likely residence"
            hints.append(
                build_hint(
                    person,
                    "Census opportunities",
                    "The chronology suggests census records may document this person across multiple households.",
                    ["Federal census schedules", "State census schedules"],
                    [f"{person.primary_name} {' '.join(str(year) for year in census_years[:4])} {place_text}"],
                    ["National Archives", "FamilySearch", "Ancestry"],
                    "medium",
                    [f"Which census years should contain {person.primary_name}?"],
                )
            )

    if born_year:
        military_queries = []
        if 1730 <= born_year <= 1767:
            military_queries.append("Revolutionary War service or pension")
        if 1815 <= born_year <= 1848:
            military_queries.append("Civil War service or pension")
        if 1872 <= born_year <= 1901:
            military_queries.append("World War I draft registration")
        if 1897 <= born_year <= 1927:
            military_queries.append("World War II draft card or enlistment")
        if military_queries:
            hints.append(
                build_hint(
                    person,
                    "Military-age record set",
                    "The birth year places this person in a historically relevant military-age cohort.",
                    military_queries,
                    [f"{person.primary_name} {military_queries[0]}"],
                    ["National Archives", "Fold3", "State military archives"],
                    "medium",
                    ["Did this person serve, register, or receive a pension?"],
                )
            )

    if len(person.source_refs) < 2 and len(person.events) < 3:
        place_text = known_place or "family locality"
        hints.append(
            build_hint(
                person,
                "Low evidence density",
                "This profile has limited event coverage and few attached citations.",
                ["Vital records sweep", "Directory search", "Land and probate search"],
                [f"{person.primary_name} records {place_text}", f"{person.primary_name} genealogy {place_text}"],
                repositories_for_place(place_text),
                "medium",
                ["Which nearby jurisdictions held the relevant records?", "Are there missing source citations already present in the original tree software?"],
            )
        )

    return hints


def build_family_migration_hints(tree: TreeData, family_ids: list[str]) -> list[Hint]:
    hints: list[Hint] = []
    for family_id in family_ids:
        family = tree.families[family_id]
        child_places = []
        for child_id in family.child_ids:
            child = tree.persons.get(child_id)
            if not child:
                continue
            birth = child.get_event("BIRT")
            if birth and birth.place:
                child_places.append(birth.place)

        if len(set(child_places)) > 1:
            husband_name = tree.persons.get(family.husband_id).primary_name if family.husband_id in tree.persons else "Unknown spouse"
            wife_name = tree.persons.get(family.wife_id).primary_name if family.wife_id in tree.persons else "Unknown spouse"
            common_places = ", ".join(place for place, _ in Counter(child_places).most_common(3))
            hints.append(
                Hint(
                    target_id=family_id,
                    target_name=f"{husband_name} / {wife_name}",
                    hint_type="Family migration clue",
                    rationale="Children in the same family were born in multiple places, suggesting migration or temporary residence changes.",
                    suggested_record_types=["Land records", "Tax lists", "City directories", "Church registers"],
                    search_queries=[f'"{husband_name}" "{wife_name}" migration {common_places}'],
                    repositories=["County courthouse", "State archives", "Local historical societies"],
                    confidence="medium",
                    unresolved_questions=["When did the family relocate between the child birthplaces?", "Was the movement permanent, seasonal, or tied to military service or work?"],
                )
            )
    return hints


def format_hints(hints: list[Hint]) -> str:
    if not hints:
        return "No hint targets were generated for the selected scope."

    blocks = []
    for index, hint in enumerate(hints, start=1):
        blocks.append(
            "\n".join(
                [
                    f"Hint {index}: {hint.hint_type}",
                    f"Target: {hint.target_name} ({hint.target_id})",
                    f"Why this hint was generated: {hint.rationale}",
                    f"Suggested record types: {', '.join(hint.suggested_record_types)}",
                    f"Search query candidates: {' | '.join(hint.search_queries)}",
                    f"Likely repositories: {', '.join(hint.repositories)}",
                    f"Confidence level: {hint.confidence}",
                    f"Unresolved questions: {' | '.join(hint.unresolved_questions)}",
                ]
            )
        )
    return "\n\n".join(blocks)


def run_hint_generation(gedcom_path: str, target_scope: str | None = None) -> tuple[str, list[Hint]]:
    tree = parse_gedcom(gedcom_path)
    person_ids, family_ids, scope_name = resolve_scope(tree, target_scope)

    hints: list[Hint] = []
    for person_id in person_ids:
        hints.extend(build_person_hints(tree.persons[person_id]))
    hints.extend(build_family_migration_hints(tree, family_ids))

    source_list = sorted(
        {
            ref.id
            for person_id in person_ids
            for ref in tree.persons[person_id].source_refs
            if ref.id
        }
    )

    write_report(
        REPORT_FILE,
        "Research Hints Report",
        gedcom_path,
        scope_name,
        [
            (
                "Summary",
                f"People reviewed: {len(person_ids)}\nFamilies reviewed: {len(family_ids)}\nHints generated: {len(hints)}",
            ),
            ("Hints by Person / Family", format_hints(hints)),
        ],
        source_list=source_list,
        confidence_notes=[
            "Hints are research suggestions, not proven facts.",
            "Prioritize hints with direct record types and clear locality clues before broader web searching.",
        ],
        next_steps=[
            "Use the external archival search workflow for the strongest hint targets.",
            "Compare new findings against the consistency report before updating the tree.",
        ],
    )
    return REPORT_FILE, hints


def main() -> None:
    gedcom_path = input("GEDCOM file path [bissell.ged]: ").strip() or "bissell.ged"
    target_scope = input("Target person or family (optional): ").strip() or None
    output, hints = run_hint_generation(gedcom_path, target_scope)
    print(f"\n[+] Research hints complete. Report written to {output}")

    if hints:
        run_search = input("Run archival search for this scope now? [y/N]: ").strip().lower()
        if run_search == "y":
            from external_recon import run_external_recon

            first_hint = hints[0]
            run_external_recon(
                target_name=first_hint.target_name,
                place="",
                record_focus=first_hint.hint_type,
                target_scope=target_scope or first_hint.target_name,
            )


if __name__ == "__main__":
    main()
