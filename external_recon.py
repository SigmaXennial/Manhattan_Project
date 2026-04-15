from __future__ import annotations

import requests

from json_export import refresh_case_bundle_artifacts
from report_utils import write_report

REPORT_FILE = "External_Recon_Report.txt"


def build_query(target_name: str, birth_year: str = "", death_year: str = "", place: str = "", record_focus: str = "") -> str:
    parts = [target_name]
    for value in [birth_year, death_year, place, record_focus]:
        if value:
            parts.append(value)
    return " ".join(parts)


def search_nara(query: str) -> list[dict[str, str]]:
    response = requests.get(
        "https://catalog.archives.gov/api/v2/records/search",
        params={"q": query, "limit": 5},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    hits = data.get("body", {}).get("hits", {}).get("hits", [])

    results = []
    for hit in hits:
        record = hit.get("_source", {}).get("record", {})
        naid = record.get("naId", "")
        results.append(
            {
                "title": record.get("title", "No title provided"),
                "date": record.get("productionDates", [{}])[0].get("logicalDate", "") if record.get("productionDates") else "",
                "url": f"https://catalog.archives.gov/id/{naid}" if naid else "",
                "repository": "National Archives Catalog",
            }
        )
    return results


def search_chronicling_america(query: str) -> list[dict[str, str]]:
    response = requests.get(
        "https://chroniclingamerica.loc.gov/search/pages/results/",
        params={"andtext": query, "format": "json"},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    items = data.get("items", [])[:5]

    results = []
    for item in items:
        results.append(
            {
                "title": item.get("title", "Unknown newspaper"),
                "date": item.get("date", ""),
                "url": f"https://chroniclingamerica.loc.gov{item.get('id', '')}",
                "repository": ", ".join(item.get("city", [])) or "Chronicling America",
            }
        )
    return results


def format_results(title: str, results: list[dict[str, str]], failure: str = "") -> str:
    if failure:
        return failure
    if not results:
        return "No results returned."

    blocks = []
    for index, result in enumerate(results, start=1):
        blocks.append(
            "\n".join(
                [
                    f"Result {index}: {result.get('title', 'Untitled')}",
                    f"Date: {result.get('date', 'Unknown') or 'Unknown'}",
                    f"Repository / Location: {result.get('repository', 'Unknown') or 'Unknown'}",
                    f"URL: {result.get('url', 'Not available') or 'Not available'}",
                ]
            )
        )
    return "\n\n".join(blocks)


def run_external_recon(
    target_name: str,
    birth_year: str = "",
    death_year: str = "",
    place: str = "",
    record_focus: str = "",
    target_scope: str | None = None,
) -> str:
    query = build_query(target_name, birth_year, death_year, place, record_focus)
    nara_results: list[dict[str, str]] = []
    newspaper_results: list[dict[str, str]] = []
    nara_failure = ""
    newspaper_failure = ""

    try:
        nara_results = search_nara(query)
    except Exception as exc:
        nara_failure = f"NARA search failed: {exc}"

    try:
        newspaper_results = search_chronicling_america(query)
    except Exception as exc:
        newspaper_failure = f"Chronicling America search failed: {exc}"

    scope_name = target_scope or target_name
    write_report(
        REPORT_FILE,
        "External Recon Report",
        "Public archival APIs",
        scope_name,
        [
            (
                "Search Profile",
                "\n".join(
                    [
                        f"Target name: {target_name}",
                        f"Birth year: {birth_year or 'Not provided'}",
                        f"Death year: {death_year or 'Not provided'}",
                        f"Place: {place or 'Not provided'}",
                        f"Research focus: {record_focus or 'General archival search'}",
                        f"Query used: {query}",
                    ]
                ),
            ),
            ("National Archives Results", format_results("National Archives Results", nara_results, nara_failure)),
            ("Historic Newspaper Results", format_results("Historic Newspaper Results", newspaper_results, newspaper_failure)),
        ],
        source_list=[
            "National Archives Catalog API",
            "Library of Congress Chronicling America API",
        ],
        confidence_notes=[
            "API search results are leads and may still require name disambiguation.",
            "Empty result sets do not prove the absence of records; try narrower or alternate-name searches.",
        ],
        next_steps=[
            "Open the strongest archival hits and extract citation-ready details into the evidence locker.",
            "Use the broad web recon workflow if public archival search returns thin results.",
        ],
    )
    refresh_case_bundle_artifacts(scope_name=scope_name)
    print(f"\n[+] External archival search complete. Report written to {REPORT_FILE}")
    return REPORT_FILE


def main() -> None:
    target_name = input("Target name: ").strip()
    if not target_name:
        print("[-] A target name is required.")
        return

    birth_year = input("Birth year (optional): ").strip()
    death_year = input("Death year (optional): ").strip()
    place = input("Place (optional): ").strip()
    record_focus = input("Record focus (optional): ").strip()
    run_external_recon(target_name, birth_year, death_year, place, record_focus)


if __name__ == "__main__":
    main()
