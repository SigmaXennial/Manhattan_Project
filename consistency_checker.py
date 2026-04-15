from __future__ import annotations

import re

from gedcom_parser import parse_gedcom, resolve_scope
from genealogy_models import ConsistencyIssue, Family, Person, TreeData
from report_utils import format_list, write_report

REPORT_FILE = "Consistency_Report.txt"


def extract_year(date_text: str) -> int | None:
    if not date_text:
        return None
    match = re.search(r"(1[5-9]\d{2}|20\d{2})", date_text)
    if not match:
        return None
    return int(match.group(1))


def person_birth_year(person: Person) -> int | None:
    event = person.get_event("BIRT")
    return extract_year(event.date if event else "")


def person_death_year(person: Person) -> int | None:
    event = person.get_event("DEAT")
    return extract_year(event.date if event else "")


def family_marriage_year(family: Family) -> int | None:
    event = family.get_event("MARR")
    return extract_year(event.date if event else "")


def display_name(tree: TreeData, person_id: str) -> str:
    person = tree.persons.get(person_id)
    return person.primary_name if person else person_id


def run_checks(tree: TreeData, person_ids: list[str], family_ids: list[str]) -> list[ConsistencyIssue]:
    issues: list[ConsistencyIssue] = []

    for person_id in person_ids:
        person = tree.persons[person_id]
        birth_year = person_birth_year(person)
        death_year = person_death_year(person)

        if birth_year and death_year and birth_year > death_year:
            issues.append(
                ConsistencyIssue(
                    issue_type="Birth after death",
                    description=f"{person.primary_name} has birth year {birth_year} after death year {death_year}.",
                    affected_ids=[person.id],
                    recommendation="Review the birth and death citations and look for transposed years or merged identities.",
                    severity="high",
                )
            )

    for family_id in family_ids:
        family = tree.families[family_id]
        marriage_year = family_marriage_year(family)
        parent_ids = [person_id for person_id in [family.husband_id, family.wife_id] if person_id in tree.persons]

        for child_id in family.child_ids:
            if child_id not in tree.persons:
                continue

            child = tree.persons[child_id]
            child_birth_year = person_birth_year(child)
            if not child_birth_year:
                continue

            if marriage_year and child_birth_year < marriage_year - 1:
                issues.append(
                    ConsistencyIssue(
                        issue_type="Child before recorded marriage",
                        description=(
                            f"{child.primary_name} has birth year {child_birth_year} earlier than the recorded marriage year "
                            f"{marriage_year} for family {family_id}."
                        ),
                        affected_ids=[family_id, child_id],
                        recommendation="Confirm the marriage date, look for an earlier union, or note that the child may predate the formal marriage record.",
                        severity="medium",
                    )
                )

            for parent_id in parent_ids:
                parent = tree.persons[parent_id]
                parent_birth_year = person_birth_year(parent)
                parent_death_year = person_death_year(parent)
                if parent_birth_year:
                    parent_age = child_birth_year - parent_birth_year
                    if parent_age < 12:
                        issues.append(
                            ConsistencyIssue(
                                issue_type="Parent implausibly young",
                                description=(
                                    f"{display_name(tree, parent_id)} would have been about {parent_age} when {child.primary_name} was born in {child_birth_year}."
                                ),
                                affected_ids=[parent_id, child_id, family_id],
                                recommendation="Check whether the parent or child birth year is misread or whether the relationship is attached to the wrong family.",
                                severity="high",
                            )
                        )
                    elif parent_age > 80:
                        issues.append(
                            ConsistencyIssue(
                                issue_type="Parent unusually old",
                                description=(
                                    f"{display_name(tree, parent_id)} would have been about {parent_age} when {child.primary_name} was born in {child_birth_year}."
                                ),
                                affected_ids=[parent_id, child_id, family_id],
                                recommendation="Review late-life parentage carefully and compare against census or probate records for the household.",
                                severity="medium",
                            )
                        )

                if parent_death_year and child_birth_year > parent_death_year + 1:
                    issues.append(
                        ConsistencyIssue(
                            issue_type="Child born after parent death",
                            description=(
                                f"{child.primary_name} has birth year {child_birth_year}, which is later than the death year {parent_death_year} "
                                f"recorded for {display_name(tree, parent_id)}."
                            ),
                            affected_ids=[parent_id, child_id, family_id],
                            recommendation="Validate the death date and confirm whether the parent-child relationship belongs to this individual.",
                            severity="high",
                        )
                    )

    seen_pairs: set[tuple[str, str]] = set()
    scoped_people = [tree.persons[person_id] for person_id in person_ids]
    for first_person in scoped_people:
        first_birth = person_birth_year(first_person)
        first_death = person_death_year(first_person)
        first_name_key = re.sub(r"[^a-z]", "", first_person.primary_name.lower())
        for second_person in scoped_people:
            if first_person.id >= second_person.id:
                continue
            pair = (first_person.id, second_person.id)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            second_birth = person_birth_year(second_person)
            second_death = person_death_year(second_person)
            second_name_key = re.sub(r"[^a-z]", "", second_person.primary_name.lower())

            shared_surname = first_person.surname and first_person.surname == second_person.surname
            similar_name = first_name_key[:6] and first_name_key[:6] == second_name_key[:6]
            overlapping_birth = first_birth and second_birth and abs(first_birth - second_birth) <= 2
            overlapping_death = not first_death or not second_death or abs(first_death - second_death) <= 2

            if shared_surname and similar_name and overlapping_birth and overlapping_death:
                issues.append(
                    ConsistencyIssue(
                        issue_type="Possible duplicate individual",
                        description=(
                            f"{first_person.primary_name} ({first_person.id}) and {second_person.primary_name} ({second_person.id}) "
                            "have very similar names and overlapping chronology."
                        ),
                        affected_ids=[first_person.id, second_person.id],
                        recommendation="Compare source citations, residences, and family links to confirm whether these are separate people or duplicate profiles.",
                        severity="medium",
                    )
                )

    return issues


def build_issue_text(issues: list[ConsistencyIssue]) -> str:
    if not issues:
        return "No chronology or relationship anomalies were detected in the selected scope."

    blocks = []
    for index, issue in enumerate(issues, start=1):
        blocks.append(
            "\n".join(
                [
                    f"Issue {index}: {issue.issue_type} [{issue.severity.upper()}]",
                    f"Affected Records: {', '.join(issue.affected_ids)}",
                    f"Why it is suspicious: {issue.description}",
                    f"Recommended next step: {issue.recommendation}",
                ]
            )
        )
    return "\n\n".join(blocks)


def run_consistency_check(gedcom_path: str, target_scope: str | None = None) -> str:
    tree = parse_gedcom(gedcom_path)
    person_ids, family_ids, scope_name = resolve_scope(tree, target_scope)
    issues = run_checks(tree, person_ids, family_ids)

    source_ids = sorted(
        {
            ref.id
            for person_id in person_ids
            for ref in tree.persons[person_id].source_refs
            if ref.id
        }
    )

    sections = [
        (
            "Summary",
            f"People reviewed: {len(person_ids)}\nFamilies reviewed: {len(family_ids)}\nIssues found: {len(issues)}",
        ),
        ("Findings by Rule", build_issue_text(issues)),
    ]

    write_report(
        REPORT_FILE,
        "Consistency Report",
        gedcom_path,
        scope_name,
        sections,
        source_list=source_ids,
        confidence_notes=[
            "These findings are deterministic checks and should be reviewed against the cited records.",
            "Absence of an issue does not prove that the tree is correct; it only means these rules did not detect a problem.",
        ],
        next_steps=[
            "Review each high-severity chronology conflict against the original GEDCOM citations.",
            "Use the hint workflow to identify records that could resolve unresolved dates or duplicate questions.",
        ],
    )
    return REPORT_FILE


def main() -> None:
    gedcom_path = input("GEDCOM file path [bissell.ged]: ").strip() or "bissell.ged"
    target_scope = input("Target person or family (optional): ").strip() or None
    output = run_consistency_check(gedcom_path, target_scope)
    print(f"\n[+] Consistency review complete. Report written to {output}")


if __name__ == "__main__":
    main()
