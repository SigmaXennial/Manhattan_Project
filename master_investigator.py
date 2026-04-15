from __future__ import annotations

from dotenv import load_dotenv
from duckduckgo_search import DDGS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langchain_tavily import TavilySearch

from json_export import refresh_case_bundle_artifacts
from report_utils import write_report

REPORT_FILE = "Broad_Web_Recon_Report.txt"

load_dotenv()


def get_research_parameters() -> dict[str, str]:
    print("\n--- Genealogy Intelligence Platform: Broad Web Recon ---")
    print("Enter the research target. Press Enter to skip optional fields.\n")

    name = input("Person or family target: ").strip()
    if not name:
        raise ValueError("A target name is required.")

    return {
        "name": name,
        "birth_date": input("Birth year/date (optional): ").strip(),
        "death_date": input("Death year/date (optional): ").strip(),
        "locations": input("Locations (optional): ").strip(),
        "records_of_interest": input("Records of interest (optional): ").strip(),
        "research_goal": input("Research goal (optional): ").strip(),
    }


def build_search_query(params: dict[str, str]) -> str:
    query_parts = [params["name"]]
    for key in ["birth_date", "death_date", "locations", "records_of_interest"]:
        if params[key]:
            query_parts.append(params[key])
    query_parts.extend(["genealogy", "historical records"])
    return " ".join(query_parts)


def run_tavily_search(query: str) -> tuple[list[dict[str, str]], str]:
    try:
        tavily_search = TavilySearch(max_results=5)
        results = tavily_search.invoke({"query": query})
        normalized = results.get("results", []) if isinstance(results, dict) else []
        return normalized, ""
    except Exception as exc:
        return [], f"Tavily search failed: {exc}"


def run_duckduckgo_search(query: str) -> tuple[list[dict[str, str]], str]:
    try:
        results = list(DDGS().text(query, max_results=5))
        return results, ""
    except Exception as exc:
        return [], f"DuckDuckGo search failed: {exc}"


def format_search_results(title: str, results: list[dict[str, str]], source_key: str, failure: str = "") -> str:
    if failure:
        return failure
    if not results:
        return "No results returned."

    blocks = []
    for index, result in enumerate(results, start=1):
        if source_key == "tavily":
            blocks.append(
                "\n".join(
                    [
                        f"Result {index}: {result.get('title', 'Untitled')}",
                        f"URL: {result.get('url', 'Not available')}",
                        f"Snippet: {result.get('content', 'No summary provided')}",
                    ]
                )
            )
        else:
            blocks.append(
                "\n".join(
                    [
                        f"Result {index}: {result.get('title', 'Untitled')}",
                        f"URL: {result.get('href', 'Not available')}",
                        f"Snippet: {result.get('body', 'No summary provided')}",
                    ]
                )
            )
    return "\n\n".join(blocks)


def synthesize_findings(params: dict[str, str], tavily_results: list[dict[str, str]], ddg_results: list[dict[str, str]], failures: list[str]) -> str:
    raw_intelligence = {
        "tavily": tavily_results,
        "duckduckgo": ddg_results,
        "failures": failures,
    }
    prompt = ChatPromptTemplate.from_template(
        """
You are a genealogical research analyst.
Review the combined public web search results for {name} and produce a concise evidence-aware briefing.
Only use information present in the search results. Separate probable facts from uncertain leads.
Also call out which result types appear promising for follow-up archival work.

Search profile:
{profile}

Results:
{results}
"""
    )

    try:
        llm = ChatOllama(model="dolphin-mixtral", temperature=0.1)
        chain = prompt | llm | StrOutputParser()
        return chain.invoke(
            {
                "name": params["name"],
                "profile": params,
                "results": raw_intelligence,
            }
        ).strip()
    except Exception as exc:
        failure_text = "; ".join(failures) if failures else "No additional failures recorded."
        return f"AI synthesis unavailable: {exc}. Raw search results are still included below. Search failures: {failure_text}"


def run_broad_recon(params: dict[str, str]) -> str:
    query = build_search_query(params)
    tavily_results, tavily_failure = run_tavily_search(query)
    ddg_results, ddg_failure = run_duckduckgo_search(query)
    failures = [failure for failure in [tavily_failure, ddg_failure] if failure]
    synthesis = synthesize_findings(params, tavily_results, ddg_results, failures)

    write_report(
        REPORT_FILE,
        "Broad Web Recon Report",
        "Tavily + DuckDuckGo",
        params["name"],
        [
            (
                "Search Profile",
                "\n".join(
                    [
                        f"Target: {params['name']}",
                        f"Birth date: {params['birth_date'] or 'Not provided'}",
                        f"Death date: {params['death_date'] or 'Not provided'}",
                        f"Locations: {params['locations'] or 'Not provided'}",
                        f"Records of interest: {params['records_of_interest'] or 'Not provided'}",
                        f"Research goal: {params['research_goal'] or 'Not provided'}",
                        f"Query used: {query}",
                    ]
                ),
            ),
            ("AI Research Briefing", synthesis),
            ("Tavily Results", format_search_results("Tavily Results", tavily_results, "tavily", tavily_failure)),
            ("DuckDuckGo Results", format_search_results("DuckDuckGo Results", ddg_results, "duckduckgo", ddg_failure)),
        ],
        source_list=["Tavily Search API", "DuckDuckGo Search"],
        confidence_notes=[
            "Broad web results may include compiled trees or derivative content that still require source verification.",
            "Prioritize original record repositories and archival descriptions over unsourced tertiary summaries.",
        ],
        next_steps=[
            "Push promising public web leads into targeted archival searches.",
            "Add useful URLs or excerpts to the evidence locker for later proof-summary assembly.",
        ],
    )
    refresh_case_bundle_artifacts(scope_name=params["name"])
    print(f"\n[+] Broad web recon complete. Report written to {REPORT_FILE}")
    return REPORT_FILE


def main() -> None:
    try:
        params = get_research_parameters()
    except ValueError as exc:
        print(f"[-] {exc}")
        return
    run_broad_recon(params)


if __name__ == "__main__":
    main()
