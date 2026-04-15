from __future__ import annotations

from pathlib import Path

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from report_utils import write_report

PROOF_REPORT = "Proof_Summary_Draft.txt"
REPORT_INPUTS = [
    "Tree_Structure_Report.txt",
    "Consistency_Report.txt",
    "Research_Hints_Report.txt",
    "External_Recon_Report.txt",
    "Broad_Web_Recon_Report.txt",
    "Transcription_Report.txt",
    "Evidence_Index.txt",
]


def collect_research_packets() -> tuple[str, list[str]]:
    packet_parts = []
    found_files = []
    for file_name in REPORT_INPUTS:
        path = Path(file_name)
        if path.exists():
            found_files.append(file_name)
            packet_parts.append(f"\n--- {file_name} ---\n{path.read_text(encoding='utf-8', errors='replace')}")
    return "\n".join(packet_parts), found_files


def compile_proof_summary() -> str | None:
    research_packet, found_files = collect_research_packets()
    if not research_packet:
        print("[-] No structured reports were found. Run tree analysis or related workflows first.")
        return None

    prompt = ChatPromptTemplate.from_template(
        """
You are a senior genealogist preparing a proof-style summary draft.
Use only the supplied reports.

Draft a structured summary with these sections:
1. Research Scope
2. Evidence Reviewed
3. Tentative Lineage / Identity Findings
4. Conflicts or Chronology Issues
5. Research Hints Worth Pursuing Next
6. Citation and Evidence Gaps

Do not present uncertain claims as proven facts.
Keep the tone formal and evidence-aware.

REPORTS:
{reports}
"""
    )

    confidence_notes = [
        "This draft is a synthesis layer over the available reports and does not replace source-by-source review.",
        "Conflicting evidence should be resolved against original records before formal submission or publication.",
    ]

    try:
        llm = ChatOllama(model="dolphin-mixtral", temperature=0.1)
        chain = prompt | llm | StrOutputParser()
        draft = chain.invoke({"reports": research_packet}).strip()
    except Exception as exc:
        draft = (
            f"AI synthesis unavailable: {exc}\n\n"
            f"Reports collected: {', '.join(found_files)}\n"
            "Use the underlying reports to assemble a manual proof summary."
        )
        confidence_notes.append("The AI synthesis step was unavailable, so this file currently contains a manual assembly note.")

    write_report(
        PROOF_REPORT,
        "Proof Summary Draft",
        ", ".join(found_files),
        "Compiled case summary",
        [("Draft Narrative", draft)],
        source_list=found_files,
        confidence_notes=confidence_notes,
        next_steps=[
            "Review each claim against the cited reports and underlying records.",
            "Promote unresolved conflicts back into the consistency and hint workflows for follow-up research.",
        ],
    )
    print(f"\n[+] Proof summary draft written to {PROOF_REPORT}")
    return PROOF_REPORT


def main() -> None:
    compile_proof_summary()


if __name__ == "__main__":
    main()
