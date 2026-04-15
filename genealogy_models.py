from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SourceReference:
    id: str = ""
    title: str = ""
    page: str = ""
    repository: str = ""
    url: str = ""
    detail: str = ""


@dataclass
class Event:
    type: str
    date: str = ""
    place: str = ""
    description: str = ""
    source_refs: list[SourceReference] = field(default_factory=list)


@dataclass
class Person:
    id: str
    primary_name: str = "Unknown"
    given_name: str = ""
    surname: str = ""
    sex: str = ""
    family_as_child: str = ""
    families_as_spouse: list[str] = field(default_factory=list)
    name_variants: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)
    source_refs: list[SourceReference] = field(default_factory=list)

    def get_event(self, event_type: str) -> Event | None:
        for event in self.events:
            if event.type == event_type:
                return event
        return None


@dataclass
class Family:
    id: str
    husband_id: str = ""
    wife_id: str = ""
    child_ids: list[str] = field(default_factory=list)
    relationship_type: str = ""
    events: list[Event] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    source_refs: list[SourceReference] = field(default_factory=list)

    def get_event(self, event_type: str) -> Event | None:
        for event in self.events:
            if event.type == event_type:
                return event
        return None


@dataclass
class Hint:
    target_id: str
    target_name: str
    hint_type: str
    rationale: str
    suggested_record_types: list[str] = field(default_factory=list)
    search_queries: list[str] = field(default_factory=list)
    repositories: list[str] = field(default_factory=list)
    confidence: str = "medium"
    unresolved_questions: list[str] = field(default_factory=list)


@dataclass
class ConsistencyIssue:
    issue_type: str
    description: str
    affected_ids: list[str] = field(default_factory=list)
    recommendation: str = ""
    severity: str = "medium"


@dataclass
class TreeData:
    gedcom_file: str
    persons: dict[str, Person] = field(default_factory=dict)
    families: dict[str, Family] = field(default_factory=dict)
    sources: dict[str, SourceReference] = field(default_factory=dict)
