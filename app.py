from __future__ import annotations

import io
import json
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any, Callable

import streamlit as st

from analyze_tree import JSON_FILE as TREE_JSON_FILE
from analyze_tree import REPORT_FILE as TREE_REPORT_FILE
from analyze_tree import run_tree_analysis
from compiler import PROOF_REPORT, compile_proof_summary
from consistency_checker import REPORT_FILE as CONSISTENCY_REPORT_FILE
from consistency_checker import run_consistency_check
from evidence_locker import organize_evidence
from external_recon import REPORT_FILE as EXTERNAL_RECON_REPORT_FILE
from external_recon import run_external_recon
from hint_engine import REPORT_FILE as HINTS_REPORT_FILE
from hint_engine import run_hint_generation
from json_export import CASE_BUNDLE_FILE, CONSISTENCY_EXPORT_FILE, HINTS_EXPORT_FILE
from master_investigator import REPORT_FILE as BROAD_RECON_REPORT_FILE
from master_investigator import run_broad_recon
from transcribe_doc import REPORT_FILE as TRANSCRIPTION_REPORT_FILE
from transcribe_doc import transcribe_document

EVIDENCE_INDEX_FILE = "Evidence_Index.txt"
DEFAULT_OUTPUTS = [
    TREE_REPORT_FILE,
    TREE_JSON_FILE,
    CONSISTENCY_REPORT_FILE,
    CONSISTENCY_EXPORT_FILE,
    HINTS_REPORT_FILE,
    HINTS_EXPORT_FILE,
    EXTERNAL_RECON_REPORT_FILE,
    BROAD_RECON_REPORT_FILE,
    TRANSCRIPTION_REPORT_FILE,
    EVIDENCE_INDEX_FILE,
    PROOF_REPORT,
    CASE_BUNDLE_FILE,
]
BROWSABLE_PATTERNS = ["*.txt", "*.json", "*.ged", "*.jpg", "*.jpeg", "*.png", "*.pdf"]


def init_state() -> None:
    defaults = {
        "gedcom_path": "bissell.ged",
        "scope": "",
        "target_name": "",
        "birth_year": "",
        "death_year": "",
        "place": "",
        "record_focus": "",
        "broad_locations": "",
        "records_of_interest": "",
        "research_goal": "operational osint",
        "image_path": "document_Page_1.jpg",
        "case_name": "",
        "activity": [],
        "selected_browser_file": CASE_BUNDLE_FILE,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


st.set_page_config(page_title="Genealogy Intelligence App", page_icon="📜", layout="wide")
init_state()

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #efe2c8 0%, #eadbc2 42%, #e4d3b7 100%);
        color: #33261a;
    }
    [data-testid="stSidebar"] {
        background: #d8c2a1;
        border-right: 1px solid rgba(71, 46, 24, 0.18);
    }
    .block-container {
        max-width: 1480px;
        padding-top: 1.2rem;
        padding-bottom: 2.4rem;
    }
    .archive-hero {
        background: linear-gradient(135deg, rgba(110, 66, 25, 0.96), rgba(75, 46, 22, 0.94));
        color: #f7ecd9;
        border: 1px solid rgba(255, 242, 220, 0.16);
        border-radius: 26px;
        padding: 1.45rem 1.6rem;
        box-shadow: 0 16px 34px rgba(69, 43, 20, 0.18);
        margin-bottom: 1rem;
    }
    .archive-card {
        background: rgba(255, 248, 236, 0.82);
        border: 1px solid rgba(108, 74, 38, 0.18);
        border-radius: 22px;
        padding: 1rem 1.05rem;
        box-shadow: 0 10px 24px rgba(85, 58, 29, 0.08);
        margin-bottom: 1rem;
    }
    .archive-note {
        background: rgba(124, 78, 31, 0.08);
        border-left: 4px solid #8a5a2b;
        border-radius: 14px;
        padding: 0.9rem 1rem;
        margin-bottom: 0.9rem;
    }
    .file-pill {
        display: inline-block;
        padding: 0.35rem 0.72rem;
        border-radius: 999px;
        margin: 0.18rem 0.35rem 0.18rem 0;
        font-size: 0.88rem;
        background: #f6ecdb;
        border: 1px solid rgba(108, 74, 38, 0.18);
        color: #5d4025;
    }
    .file-pill-ready {
        background: #efe5d0;
        color: #4f6e38;
        border-color: rgba(79, 110, 56, 0.28);
    }
    .file-pill-missing {
        color: #8a7358;
        border-color: rgba(108, 74, 38, 0.12);
    }
    .stButton > button,
    .stDownloadButton > button {
        border-radius: 999px;
        border: 1px solid #7a4b24;
        background: #8a5a2b;
        color: #fff8ef;
        font-weight: 700;
    }
    .stTextInput input, .stTextArea textarea {
        border-radius: 16px;
        background: rgba(255, 251, 244, 0.95);
    }
    div[data-testid="stMetric"] {
        background: rgba(255, 248, 236, 0.82);
        border: 1px solid rgba(108, 74, 38, 0.18);
        padding: 0.85rem;
        border-radius: 18px;
        box-shadow: 0 8px 18px rgba(85, 58, 29, 0.06);
    }
    h1, h2, h3, h4 {
        color: #4c321c;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def read_text_file(path: str) -> str:
    file_path = Path(path)
    if not file_path.exists():
        return ""
    return file_path.read_text(encoding="utf-8", errors="replace")



def read_json_file(path: str) -> dict[str, Any] | None:
    file_path = Path(path)
    if not file_path.exists():
        return None
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return None



def file_exists(path: str) -> bool:
    return Path(path).exists()



def add_activity(prompt: str, response: str, files: list[str] | None = None, logs: str = "") -> None:
    st.session_state.activity.append(
        {
            "prompt": prompt,
            "response": response,
            "files": files or [],
            "logs": logs.strip(),
        }
    )



def run_with_capture(action_name: str, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[Any, str, str | None]:
    buffer = io.StringIO()
    try:
        with redirect_stdout(buffer):
            result = fn(*args, **kwargs)
        return result, buffer.getvalue(), None
    except Exception as exc:
        return None, buffer.getvalue(), f"{action_name} failed: {exc}"



def format_scope(scope: str) -> str:
    return scope.strip() or "Entire tree"



def list_workspace_files() -> list[str]:
    discovered: dict[str, Path] = {}
    for path in [Path(file_name) for file_name in DEFAULT_OUTPUTS]:
        if path.exists() and path.is_file():
            discovered[str(path)] = path
    for pattern in BROWSABLE_PATTERNS:
        for path in Path(".").glob(pattern):
            if path.is_file() and path.parent == Path("."):
                discovered[str(path)] = path
    return sorted(discovered.keys())



def browser_default_file() -> str:
    selected = st.session_state.selected_browser_file
    if selected and file_exists(selected):
        return selected
    files = list_workspace_files()
    return files[0] if files else ""



def render_file_status(paths: list[str]) -> None:
    pills = []
    for path in paths:
        css_class = "file-pill-ready" if file_exists(path) else "file-pill-missing"
        pills.append(f"<span class='file-pill {css_class}'>{path}</span>")
    st.markdown("".join(pills), unsafe_allow_html=True)



def render_text_preview(title: str, path: str, height: int = 320) -> None:
    content = read_text_file(path)
    with st.expander(title, expanded=False):
        if content:
            st.text_area(title, value=content, height=height, key=f"text::{title}::{path}")
        else:
            st.caption("File not available yet.")



def render_json_preview(title: str, path: str) -> None:
    payload = read_json_file(path)
    with st.expander(title, expanded=False):
        if payload is None:
            st.caption("File not available yet.")
        else:
            st.json(payload)



def render_activity_feed() -> None:
    st.subheader("Operations feed")
    if not st.session_state.activity:
        st.markdown(
            "<div class='archive-note'><strong>No operations logged yet.</strong><br/>Start with the guided workflow, then move into archival or web OSINT runs.</div>",
            unsafe_allow_html=True,
        )
        return

    for item in reversed(st.session_state.activity):
        with st.chat_message("user"):
            st.markdown(item["prompt"])
        with st.chat_message("assistant"):
            st.markdown(item["response"])
            if item["files"]:
                st.caption("Updated files")
                render_file_status(item["files"])
            if item["logs"]:
                with st.expander("Console output"):
                    st.code(item["logs"])



def recommended_next_step() -> str:
    if not file_exists(TREE_JSON_FILE):
        return "Run tree analysis to establish the active case structure."
    if not file_exists(CONSISTENCY_EXPORT_FILE):
        return "Run the consistency review to surface chronology and relationship conflicts."
    if not file_exists(HINTS_EXPORT_FILE):
        return "Generate research hints to create the next research queue."
    if not file_exists(EXTERNAL_RECON_REPORT_FILE):
        return "Run external archival recon for targeted record discovery."
    if not file_exists(BROAD_RECON_REPORT_FILE):
        return "Run broad web recon to widen OSINT lead generation."
    if not file_exists(PROOF_REPORT):
        return "Compile the proof summary to consolidate findings."
    return "Review the case bundle and evidence index, then continue person-level follow-up."



def render_sidebar() -> None:
    st.sidebar.markdown("## Case control")
    st.sidebar.text_input("GEDCOM file", key="gedcom_path")
    st.sidebar.text_input("Scope / target", key="scope", placeholder="Entire tree or person name")
    st.sidebar.text_input("Operational target", key="target_name", placeholder="Used for recon workflows")
    st.sidebar.text_input("Document image", key="image_path")
    st.sidebar.text_input("Case name", key="case_name")

    st.sidebar.markdown("### Research defaults")
    st.sidebar.text_input("Birth year", key="birth_year")
    st.sidebar.text_input("Death year", key="death_year")
    st.sidebar.text_input("Place", key="place")
    st.sidebar.text_input("Record focus", key="record_focus")
    st.sidebar.text_input("OSINT locations", key="broad_locations")
    st.sidebar.text_input("Records of interest", key="records_of_interest")
    st.sidebar.text_input("Research goal", key="research_goal")

    st.sidebar.markdown("### Output status")
    for path in DEFAULT_OUTPUTS:
        marker = "●" if file_exists(path) else "○"
        st.sidebar.caption(f"{marker} {path}")

    st.sidebar.markdown("### Recommended next step")
    st.sidebar.caption(recommended_next_step())



def render_workspace_summary() -> None:
    bundle = read_json_file(CASE_BUNDLE_FILE) or {}
    person_counts = bundle.get("person_artifact_counts") or {}
    artifacts = bundle.get("artifacts") or []

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ready outputs", sum(1 for path in DEFAULT_OUTPUTS if file_exists(path)))
    c2.metric("Bundle artifacts", len(artifacts))
    c3.metric("Mapped people", person_counts.get("people_mapped", 0))
    c4.metric("Direct person artifact links", person_counts.get("people_with_direct_artifacts", 0))



def render_dashboard() -> None:
    st.markdown("### Case dashboard")
    render_workspace_summary()

    left, right = st.columns([1.05, 0.95])
    with left:
        st.markdown("<div class='archive-card'>", unsafe_allow_html=True)
        st.markdown("#### Active case profile")
        st.write(
            {
                "gedcom": st.session_state.gedcom_path,
                "scope": format_scope(st.session_state.scope),
                "operational_target": st.session_state.target_name or format_scope(st.session_state.scope),
                "document_image": st.session_state.image_path,
                "research_goal": st.session_state.research_goal or "Not set",
            }
        )
        st.markdown("#### Known outputs")
        render_file_status(DEFAULT_OUTPUTS)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='archive-card'>", unsafe_allow_html=True)
        st.markdown("#### Operational OSINT board")
        st.markdown(
            "- **Archival recon** for record repositories, catalog hits, and newspapers\n"
            "- **Broad web recon** for public lead expansion and derivative tree discovery\n"
            "- **Evidence locker** for case packaging and reviewable artifacts\n"
            "- **Case bundle** for person-linked issues, hints, and files"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='archive-card'>", unsafe_allow_html=True)
        st.markdown("#### Next recommended action")
        st.markdown(f"<div class='archive-note'>{recommended_next_step()}</div>", unsafe_allow_html=True)
        st.markdown("#### Fast previews")
        render_text_preview("External recon snapshot", EXTERNAL_RECON_REPORT_FILE, height=220)
        render_text_preview("Broad web recon snapshot", BROAD_RECON_REPORT_FILE, height=220)
        st.markdown("</div>", unsafe_allow_html=True)

    render_activity_feed()



def run_guided_workflow_ui(gedcom_path: str, scope: str, compile_summary: bool, refresh_evidence: bool) -> None:
    prompt = f"Run guided workflow for **{gedcom_path}** in scope **{format_scope(scope)}**"
    buffer = io.StringIO()
    errors: list[str] = []
    hints_count = 0

    try:
        with redirect_stdout(buffer):
            run_tree_analysis(gedcom_path, scope or None)
            run_consistency_check(gedcom_path, scope or None)
            _, hints = run_hint_generation(gedcom_path, scope or None)
            hints_count = len(hints)
            if compile_summary:
                compile_proof_summary()
            if refresh_evidence:
                organize_evidence(scope or "General Research")
    except Exception as exc:
        errors.append(str(exc))

    files = [
        TREE_REPORT_FILE,
        TREE_JSON_FILE,
        CONSISTENCY_REPORT_FILE,
        CONSISTENCY_EXPORT_FILE,
        HINTS_REPORT_FILE,
        HINTS_EXPORT_FILE,
        CASE_BUNDLE_FILE,
    ]
    if compile_summary:
        files.append(PROOF_REPORT)
    if refresh_evidence:
        files.append(EVIDENCE_INDEX_FILE)

    if errors:
        add_activity(prompt, f"The guided workflow stopped early: {errors[0]}", files, buffer.getvalue())
    else:
        add_activity(
            prompt,
            f"Finished the guided workflow. Generated tree analysis, consistency review, and {hints_count} research hints.",
            files,
            buffer.getvalue(),
        )



def render_operations_tab() -> None:
    st.markdown("### Operations")
    st.caption("Run the core genealogy workflows and the two OSINT modes from one place.")

    top_left, top_right = st.columns(2)
    with top_left:
        with st.form("guided-workflow-form"):
            st.markdown("#### Guided case build")
            guided_compile = st.checkbox("Compile proof summary after analysis", value=True)
            guided_evidence = st.checkbox("Refresh evidence locker after analysis", value=False)
            submitted = st.form_submit_button("Run guided workflow")
        if submitted:
            run_guided_workflow_ui(st.session_state.gedcom_path, st.session_state.scope, guided_compile, guided_evidence)
            st.rerun()

        with st.form("external-recon-form"):
            st.markdown("#### Archival OSINT")
            external_target = st.text_input("Target name", value=st.session_state.target_name or st.session_state.scope)
            external_birth = st.text_input("Birth year", value=st.session_state.birth_year)
            external_death = st.text_input("Death year", value=st.session_state.death_year)
            external_place = st.text_input("Place", value=st.session_state.place)
            external_focus = st.text_input("Record focus", value=st.session_state.record_focus or "operational osint")
            external_submit = st.form_submit_button("Run external recon")
        if external_submit:
            _, logs, error = run_with_capture(
                "External recon",
                run_external_recon,
                external_target,
                external_birth,
                external_death,
                external_place,
                external_focus,
                external_target or None,
            )
            if error:
                add_activity("Run external archival search", error, [EXTERNAL_RECON_REPORT_FILE, CASE_BUNDLE_FILE], logs)
            else:
                add_activity("Run external archival search", "External archival recon report updated.", [EXTERNAL_RECON_REPORT_FILE, CASE_BUNDLE_FILE], logs)
            st.rerun()

    with top_right:
        with st.form("broad-recon-form"):
            st.markdown("#### Broad web OSINT")
            broad_name = st.text_input("Person or family target", value=st.session_state.target_name or st.session_state.scope, key="broad_name_input")
            broad_birth = st.text_input("Birth year/date", value=st.session_state.birth_year, key="broad_birth_input")
            broad_death = st.text_input("Death year/date", value=st.session_state.death_year, key="broad_death_input")
            broad_locations = st.text_input("Locations", value=st.session_state.broad_locations)
            broad_records = st.text_input("Records of interest", value=st.session_state.records_of_interest)
            broad_goal = st.text_input("Research goal", value=st.session_state.research_goal)
            broad_submit = st.form_submit_button("Run broad web recon")
        if broad_submit:
            params = {
                "name": broad_name,
                "birth_date": broad_birth,
                "death_date": broad_death,
                "locations": broad_locations,
                "records_of_interest": broad_records,
                "research_goal": broad_goal,
            }
            _, logs, error = run_with_capture("Broad web recon", run_broad_recon, params)
            if error:
                add_activity("Run broad web recon", error, [BROAD_RECON_REPORT_FILE, CASE_BUNDLE_FILE], logs)
            else:
                add_activity("Run broad web recon", "Broad web recon report updated.", [BROAD_RECON_REPORT_FILE, CASE_BUNDLE_FILE], logs)
            st.rerun()

        st.markdown("<div class='archive-card'>", unsafe_allow_html=True)
        st.markdown("#### Workflow sequence")
        st.markdown(
            "1. Tree analysis\n"
            "2. Consistency review\n"
            "3. Research hints\n"
            "4. Archival OSINT\n"
            "5. Broad web OSINT\n"
            "6. Evidence and proof assembly"
        )
        st.markdown("</div>", unsafe_allow_html=True)



def render_tree_tools_tab() -> None:
    st.markdown("### Tree analysis tools")
    left, right = st.columns([0.92, 1.08])
    with left:
        with st.form("tree-analysis-form"):
            st.markdown("#### Tree structure")
            tree_submit = st.form_submit_button("Run tree analysis")
        if tree_submit:
            _, logs, error = run_with_capture("Tree analysis", run_tree_analysis, st.session_state.gedcom_path, st.session_state.scope or None)
            if error:
                add_activity("Run tree analysis", error, [TREE_REPORT_FILE, TREE_JSON_FILE, CASE_BUNDLE_FILE], logs)
            else:
                add_activity("Run tree analysis", "Tree structure report and JSON export updated.", [TREE_REPORT_FILE, TREE_JSON_FILE, CASE_BUNDLE_FILE], logs)
            st.rerun()

        with st.form("consistency-form"):
            st.markdown("#### Consistency review")
            consistency_submit = st.form_submit_button("Run consistency check")
        if consistency_submit:
            _, logs, error = run_with_capture("Consistency check", run_consistency_check, st.session_state.gedcom_path, st.session_state.scope or None)
            if error:
                add_activity("Run consistency check", error, [CONSISTENCY_REPORT_FILE, CONSISTENCY_EXPORT_FILE, CASE_BUNDLE_FILE], logs)
            else:
                add_activity("Run consistency check", "Consistency report and JSON export updated.", [CONSISTENCY_REPORT_FILE, CONSISTENCY_EXPORT_FILE, CASE_BUNDLE_FILE], logs)
            st.rerun()

        with st.form("hints-form"):
            st.markdown("#### Research hints")
            hints_submit = st.form_submit_button("Generate research hints")
        if hints_submit:
            result, logs, error = run_with_capture("Research hints", run_hint_generation, st.session_state.gedcom_path, st.session_state.scope or None)
            if error:
                add_activity("Generate research hints", error, [HINTS_REPORT_FILE, HINTS_EXPORT_FILE, CASE_BUNDLE_FILE], logs)
            else:
                _, hints = result
                add_activity(
                    "Generate research hints",
                    f"Research hints updated with {len(hints)} suggestions.",
                    [HINTS_REPORT_FILE, HINTS_EXPORT_FILE, CASE_BUNDLE_FILE],
                    logs,
                )
            st.rerun()

    with right:
        render_text_preview("Tree report preview", TREE_REPORT_FILE)
        render_json_preview("Tree JSON preview", TREE_JSON_FILE)
        render_text_preview("Consistency report preview", CONSISTENCY_REPORT_FILE)
        render_json_preview("Consistency JSON preview", CONSISTENCY_EXPORT_FILE)
        render_text_preview("Hints report preview", HINTS_REPORT_FILE)
        render_json_preview("Hints JSON preview", HINTS_EXPORT_FILE)



def render_file_browser_tab() -> None:
    st.markdown("### Report and file browser")
    files = list_workspace_files()
    if not files:
        st.info("No browseable workspace files are available yet.")
        return

    left, right = st.columns([0.72, 1.28])
    with left:
        selected_file = st.selectbox(
            "Choose a file",
            files,
            index=files.index(browser_default_file()) if browser_default_file() in files else 0,
        )
        st.session_state.selected_browser_file = selected_file
        path = Path(selected_file)
        st.markdown("<div class='archive-card'>", unsafe_allow_html=True)
        st.markdown("#### File details")
        st.write(
            {
                "name": path.name,
                "suffix": path.suffix.lower() or "none",
                "size_bytes": path.stat().st_size,
                "modified": path.stat().st_mtime,
            }
        )
        with path.open("rb") as handle:
            st.download_button("Download file", handle.read(), file_name=path.name)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        suffix = Path(selected_file).suffix.lower()
        if suffix == ".json":
            payload = read_json_file(selected_file)
            if payload is None:
                st.warning("Unable to parse this JSON file.")
            else:
                st.json(payload)
        elif suffix in {".jpg", ".jpeg", ".png"}:
            st.image(selected_file, caption=selected_file, use_container_width=True)
        else:
            content = read_text_file(selected_file)
            if content:
                st.text_area("File preview", value=content, height=620, key=f"browser::{selected_file}")
            else:
                st.info("Preview not available for this file type. Use download instead.")



def render_bundle_explorer() -> None:
    bundle = read_json_file(CASE_BUNDLE_FILE)
    if bundle is None:
        st.info("Run a workflow that generates `Case_Bundle.json` first.")
        return

    tree_section = (bundle.get("sections") or {}).get("tree") or {}
    consistency_section = (bundle.get("sections") or {}).get("consistency") or {}
    hints_section = (bundle.get("sections") or {}).get("hints") or {}
    person_artifacts = bundle.get("person_artifacts") or []
    artifact_counts = bundle.get("artifact_counts") or {}
    person_counts = bundle.get("person_artifact_counts") or {}

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("People in scope", (tree_section.get("counts") or {}).get("people_in_scope", 0))
    c2.metric("Issues", (consistency_section.get("counts") or {}).get("issues_found", 0))
    c3.metric("Hints", (hints_section.get("counts") or {}).get("hints_generated", 0))
    c4.metric("Artifacts", len(bundle.get("artifacts") or []))

    st.markdown("#### Bundle context")
    st.write(
        {
            "generated_at": bundle.get("generated_at"),
            "input_file": bundle.get("input_file"),
            "scope": bundle.get("scope"),
            "available_sections": bundle.get("available_sections"),
        }
    )

    left, right = st.columns([1.15, 0.85])
    with left:
        st.markdown("#### Person explorer")
        if not person_artifacts:
            st.caption("No person mappings yet. Run tree analysis to populate them.")
        else:
            options = {
                f"{person['person_name']} ({person['person_id']})": person for person in person_artifacts
            }
            selected_label = st.selectbox("Choose a person", list(options.keys()))
            selected = options[selected_label]
            st.write(
                {
                    "person_id": selected.get("person_id"),
                    "primary_scope_match": selected.get("is_primary_scope_match"),
                    "name_variants": selected.get("name_variants"),
                }
            )
            st.markdown("**Case artifact refs**")
            st.json(selected.get("case_artifact_refs") or [])
            st.markdown("**Direct artifact refs**")
            st.json(selected.get("direct_artifact_refs") or [])
            st.markdown("**Related consistency issues**")
            st.json(selected.get("related_issue_refs") or [])
            st.markdown("**Related research hints**")
            st.json(selected.get("related_hint_refs") or [])

    with right:
        st.markdown("#### Artifact summaries")
        st.json(artifact_counts)
        st.markdown("#### Person mapping summaries")
        st.json(person_counts)

    render_json_preview("Raw case bundle JSON", CASE_BUNDLE_FILE)



def render_documents_tab() -> None:
    st.markdown("### Documents and case assembly")
    left, right = st.columns([0.92, 1.08])
    with left:
        with st.form("transcription-form"):
            st.markdown("#### Document transcription")
            transcription_submit = st.form_submit_button("Transcribe document")
        if transcription_submit:
            _, logs, error = run_with_capture("Document transcription", transcribe_document, st.session_state.image_path)
            if error:
                add_activity("Transcribe document", error, [TRANSCRIPTION_REPORT_FILE, CASE_BUNDLE_FILE], logs)
            else:
                add_activity("Transcribe document", "Transcription report updated.", [TRANSCRIPTION_REPORT_FILE, CASE_BUNDLE_FILE], logs)
            st.rerun()

        with st.form("proof-form"):
            st.markdown("#### Proof summary")
            proof_submit = st.form_submit_button("Compile proof summary")
        if proof_submit:
            _, logs, error = run_with_capture("Proof summary", compile_proof_summary)
            if error:
                add_activity("Compile proof summary", error, [PROOF_REPORT, CASE_BUNDLE_FILE], logs)
            else:
                add_activity("Compile proof summary", "Proof summary draft updated.", [PROOF_REPORT, CASE_BUNDLE_FILE], logs)
            st.rerun()

        with st.form("evidence-form"):
            st.markdown("#### Evidence locker")
            evidence_submit = st.form_submit_button("Refresh evidence locker")
        if evidence_submit:
            _, logs, error = run_with_capture("Evidence locker", organize_evidence, st.session_state.case_name or st.session_state.scope or None)
            if error:
                add_activity("Refresh evidence locker", error, [EVIDENCE_INDEX_FILE, CASE_BUNDLE_FILE], logs)
            else:
                add_activity("Refresh evidence locker", "Evidence locker and evidence index updated.", [EVIDENCE_INDEX_FILE, CASE_BUNDLE_FILE], logs)
            st.rerun()

    with right:
        render_text_preview("Transcription report", TRANSCRIPTION_REPORT_FILE)
        render_text_preview("Proof summary preview", PROOF_REPORT)
        render_text_preview("Evidence index preview", EVIDENCE_INDEX_FILE)


render_sidebar()

st.markdown(
    """
    <div class="archive-hero">
        <h1 style="margin:0; color:#f7ecd9;">Genealogy Intelligence App</h1>
        <p style="margin:0.45rem 0 0 0; color:#f2e3c9; font-size:1.04rem;">
            A warm archival workspace for case review, report browsing, and operational OSINT across genealogy evidence.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_dashboard, tab_operations, tab_tree, tab_files, tab_bundle, tab_documents = st.tabs(
    [
        "Dashboard",
        "Operations",
        "Tree tools",
        "Reports & files",
        "People & case bundle",
        "Documents & evidence",
    ]
)

with tab_dashboard:
    render_dashboard()

with tab_operations:
    render_operations_tab()

with tab_tree:
    render_tree_tools_tab()

with tab_files:
    render_file_browser_tab()

with tab_bundle:
    render_bundle_explorer()

with tab_documents:
    render_documents_tab()
