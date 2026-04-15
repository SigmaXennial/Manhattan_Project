from __future__ import annotations

import re
from pathlib import Path

from genealogy_models import Event, Family, Person, SourceReference, TreeData

EVENT_TAGS = {"BIRT", "DEAT", "BURI", "CHR", "BAPM", "MARR", "DIV", "RESI", "CENS", "OCCU", "EMIG", "IMMI"}


GEDCOM_LINE_RE = re.compile(r"^(\d+)\s+(?:(@[^@]+@)\s+)?([A-Z0-9_]+)(?:\s+(.*))?$")


def parse_gedcom_line(line: str) -> tuple[int, str | None, str, str]:
    match = GEDCOM_LINE_RE.match(line.rstrip())
    if not match:
        raise ValueError(f"Unsupported GEDCOM line: {line}")
    level = int(match.group(1))
    xref_id = match.group(2)
    tag = match.group(3)
    value = (match.group(4) or "").strip()
    return level, xref_id, tag, value


def clean_name(name: str) -> str:
    return name.replace("/", "").strip() or "Unknown"


def create_source_ref(value: str) -> SourceReference:
    if value.startswith("@") and value.endswith("@"):
        return SourceReference(id=value)
    return SourceReference(title=value)


def append_text(existing: str, addition: str) -> str:
    if not addition:
        return existing
    if not existing:
        return addition
    return f"{existing} {addition}".strip()


def enrich_source_refs(tree: TreeData) -> None:
    def fill_from_catalog(ref: SourceReference) -> None:
        if not ref.id or ref.id not in tree.sources:
            return
        catalog = tree.sources[ref.id]
        if not ref.title:
            ref.title = catalog.title
        if not ref.repository:
            ref.repository = catalog.repository
        if not ref.url:
            ref.url = catalog.url
        if not ref.detail:
            ref.detail = catalog.detail

    for person in tree.persons.values():
        for source_ref in person.source_refs:
            fill_from_catalog(source_ref)
        for event in person.events:
            for source_ref in event.source_refs:
                fill_from_catalog(source_ref)

    for family in tree.families.values():
        for source_ref in family.source_refs:
            fill_from_catalog(source_ref)
        for event in family.events:
            for source_ref in event.source_refs:
                fill_from_catalog(source_ref)


def parse_gedcom(path: str) -> TreeData:
    tree = TreeData(gedcom_file=path)
    current_record_type = ""
    current_person: Person | None = None
    current_family: Family | None = None
    current_source: SourceReference | None = None
    current_event: Event | None = None
    current_event_level: int | None = None
    current_source_ref: SourceReference | None = None
    current_source_level: int | None = None

    for raw_line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw_line.strip():
            continue

        level, xref_id, tag, value = parse_gedcom_line(raw_line)

        if current_source_ref is not None and current_source_level is not None and level <= current_source_level:
            current_source_ref = None
            current_source_level = None

        if current_event is not None and current_event_level is not None and level <= current_event_level:
            current_event = None
            current_event_level = None

        if level == 0:
            current_person = None
            current_family = None
            current_source = None
            current_source_ref = None
            current_source_level = None
            current_event = None
            current_event_level = None
            current_record_type = tag

            if tag == "INDI" and xref_id:
                current_person = Person(id=xref_id)
                tree.persons[xref_id] = current_person
            elif tag == "FAM" and xref_id:
                current_family = Family(id=xref_id)
                tree.families[xref_id] = current_family
            elif tag == "SOUR" and xref_id:
                current_source = SourceReference(id=xref_id)
                tree.sources[xref_id] = current_source
            continue

        if current_record_type == "INDI" and current_person is not None:
            if level == 1 and tag == "NAME":
                cleaned = clean_name(value)
                if current_person.primary_name == "Unknown":
                    current_person.primary_name = cleaned
                elif cleaned not in current_person.name_variants:
                    current_person.name_variants.append(cleaned)
            elif level == 2 and tag == "GIVN":
                current_person.given_name = value
            elif level == 2 and tag == "SURN":
                current_person.surname = value
            elif level == 1 and tag == "SEX":
                current_person.sex = value
            elif level == 1 and tag == "FAMC":
                current_person.family_as_child = value
            elif level == 1 and tag == "FAMS" and value and value not in current_person.families_as_spouse:
                current_person.families_as_spouse.append(value)
            elif level == 1 and tag == "NOTE" and value:
                current_person.notes.append(value)
            elif level == 1 and tag in EVENT_TAGS:
                current_event = Event(type=tag)
                current_event_level = level
                current_person.events.append(current_event)
            elif level == 1 and tag == "SOUR":
                current_source_ref = create_source_ref(value)
                current_source_level = level
                current_person.source_refs.append(current_source_ref)
            elif current_event is not None and level >= 2:
                if tag == "DATE":
                    current_event.date = append_text(current_event.date, value)
                elif tag == "PLAC":
                    current_event.place = append_text(current_event.place, value)
                elif tag == "NOTE":
                    current_event.description = append_text(current_event.description, value)
                elif tag == "SOUR":
                    current_source_ref = create_source_ref(value)
                    current_source_level = level
                    current_event.source_refs.append(current_source_ref)
            elif current_source_ref is not None:
                if tag == "PAGE":
                    current_source_ref.page = append_text(current_source_ref.page, value)
                elif tag == "WWW":
                    current_source_ref.url = value
                elif tag in {"TEXT", "NOTE", "_APID", "AUTH", "REPO"}:
                    current_source_ref.detail = append_text(current_source_ref.detail, value)
                elif tag == "TITL":
                    current_source_ref.title = append_text(current_source_ref.title, value)

        elif current_record_type == "FAM" and current_family is not None:
            if level == 1 and tag == "HUSB":
                current_family.husband_id = value
            elif level == 1 and tag == "WIFE":
                current_family.wife_id = value
            elif level == 1 and tag == "CHIL" and value:
                current_family.child_ids.append(value)
            elif level == 1 and tag == "NOTE" and value:
                current_family.notes.append(value)
            elif level == 1 and tag in EVENT_TAGS:
                current_event = Event(type=tag)
                current_event_level = level
                current_family.events.append(current_event)
            elif level == 1 and tag == "SOUR":
                current_source_ref = create_source_ref(value)
                current_source_level = level
                current_family.source_refs.append(current_source_ref)
            elif current_event is not None and level >= 2:
                if tag == "DATE":
                    current_event.date = append_text(current_event.date, value)
                elif tag == "PLAC":
                    current_event.place = append_text(current_event.place, value)
                elif tag == "NOTE":
                    current_event.description = append_text(current_event.description, value)
                elif tag == "SOUR":
                    current_source_ref = create_source_ref(value)
                    current_source_level = level
                    current_event.source_refs.append(current_source_ref)
            elif current_source_ref is not None:
                if tag == "PAGE":
                    current_source_ref.page = append_text(current_source_ref.page, value)
                elif tag == "WWW":
                    current_source_ref.url = value
                elif tag in {"TEXT", "NOTE", "_APID", "AUTH", "REPO"}:
                    current_source_ref.detail = append_text(current_source_ref.detail, value)
                elif tag == "TITL":
                    current_source_ref.title = append_text(current_source_ref.title, value)

        elif current_record_type == "SOUR" and current_source is not None:
            if tag in {"TITL", "ABBR"}:
                current_source.title = append_text(current_source.title, value)
            elif tag in {"AUTH", "PUBL", "TEXT"}:
                current_source.detail = append_text(current_source.detail, value)
            elif tag == "REPO":
                current_source.repository = value
            elif tag == "PAGE":
                current_source.page = append_text(current_source.page, value)
            elif tag == "WWW":
                current_source.url = value

    enrich_source_refs(tree)
    return tree


def find_matching_person_ids(tree: TreeData, target_query: str | None) -> list[str]:
    if not target_query or not target_query.strip():
        return sorted(tree.persons.keys())

    query = target_query.strip().lower()
    matches = []
    for person_id, person in tree.persons.items():
        haystacks = [person_id.lower(), person.primary_name.lower()]
        haystacks.extend(name.lower() for name in person.name_variants)
        if any(query in text for text in haystacks):
            matches.append(person_id)
    return sorted(matches)


def resolve_scope(tree: TreeData, target_query: str | None) -> tuple[list[str], list[str], str]:
    matched_ids = find_matching_person_ids(tree, target_query)
    if not target_query or not target_query.strip():
        return matched_ids, sorted(tree.families.keys()), "Entire tree"

    relevant_person_ids = set(matched_ids)
    relevant_family_ids: set[str] = set()

    for family_id, family in tree.families.items():
        family_people = {family.husband_id, family.wife_id, *family.child_ids}
        if relevant_person_ids.intersection(person_id for person_id in family_people if person_id):
            relevant_family_ids.add(family_id)
            relevant_person_ids.update(person_id for person_id in family_people if person_id)

    scope_label = target_query if matched_ids else f"No direct matches for '{target_query}'"
    return sorted(relevant_person_ids), sorted(relevant_family_ids), scope_label
