from __future__ import annotations

from datetime import datetime
from pathlib import Path


def timestamp_label() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def scope_label(target_scope: str | None) -> str:
    if target_scope and target_scope.strip():
        return target_scope.strip()
    return "Entire tree"


def format_list(items: list[str], empty_message: str = "None") -> str:
    cleaned = [item.strip() for item in items if item and item.strip()]
    if not cleaned:
        return empty_message
    return "\n".join(f"- {item}" for item in cleaned)


def build_report_header(title: str, input_file: str, target_scope: str | None) -> str:
    return "\n".join(
        [
            title,
            "=" * len(title),
            f"Generated: {timestamp_label()}",
            f"Input File: {input_file}",
            f"Scope: {scope_label(target_scope)}",
        ]
    )


def make_section(title: str, content: str) -> str:
    clean_content = content.strip() if content.strip() else "None"
    return f"\n\n{title}\n{'-' * len(title)}\n{clean_content}"


def write_report(
    output_path: str,
    title: str,
    input_file: str,
    target_scope: str | None,
    sections: list[tuple[str, str]],
    source_list: list[str] | None = None,
    confidence_notes: list[str] | None = None,
    next_steps: list[str] | None = None,
) -> str:
    parts = [build_report_header(title, input_file, target_scope)]

    for section_title, section_content in sections:
        parts.append(make_section(section_title, section_content))

    if source_list is not None:
        parts.append(make_section("Source List", format_list(source_list)))

    if confidence_notes is not None:
        parts.append(make_section("Confidence / Uncertainty Notes", format_list(confidence_notes)))

    if next_steps is not None:
        parts.append(make_section("Next-Step Recommendations", format_list(next_steps)))

    Path(output_path).write_text("".join(parts).strip() + "\n", encoding="utf-8")
    return output_path
