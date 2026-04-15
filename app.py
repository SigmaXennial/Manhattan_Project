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
        "research_goal": "",
        "image_path": "document_Page_1.jpg",
        "case_name": "",
        "activity": [],
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


st.set_page_config(page_title="Genealogy Workspace", page_icon="🧬", layout="wide")
init_state()

st.markdown(

    """
    <style>
    .stApp {
        background: #131314;
        color: #e3e3e3;
    }
    [data-testid="stSidebar"] {
        background: #1d1e20;
        border-right: 1px solid #2a2b2e;
    }
    .block-container {
        max-width: 1440px;
        padding-top: 1.75rem;
        padding-bottom: 2.5rem;
    }
    .gem-hero {
        background: linear-gradient(135deg, rgba(138,180,248,0.16), rgba(129,201,149,0.08));
        border: 1px solid rgba(138,180,248,0.2);
        border-radius: 24px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1rem;
    }
    .gem-card {
        background: #1e1f20;
        border: 1px solid #2b2d31;
        border-radius: 20px;
        padding: 1rem 1.1rem;
        margin-bottom: 1rem;
    }
    .file-pill {
        display: inline-block;
        padding: 0.35rem 0.7rem;
        border-radius: 999px;
        margin: 0.2rem 0.35rem 0.2rem 0;
        font-size: 0.9rem;
        background: #24262a;
        border: 1px solid #31343a;
    }
    .ok-pill {
        color: #9fe6b0;
        border-color: rgba(129, 201, 149, 0.3);
    }
    .muted-pill {
        color: #b8bcc5;
    }
    .stButton > button,
    .stDownloadButton > button {
        border-radius: 999px;
        border: 1px solid #3a5fd7;
        background: #2d63ff;
        color: white;
        font-weight: 600;
    }
    .stTextInput input, .stTextArea textarea {
        border-radius: 16px;
    }
    div[data-testid="stMetric"] {
        background: #1e1f20;
        border: 1px solid #2b2d31;
        padding: 0.8rem;
        border-radius: 18px;
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


def render_activity_feed() -> None:
    st.subheader("Workspace feed")
    if not st.session_state.activity:
        with st.chat_message("assistant"):
            st.markdown(
                "Start with **Guided workflow** to build a case bundle, then use the explorer to review people, issues, hints, and artifacts."
            )
        return

    for item in reversed(st.session_state.activity):
        with st.chat_message("user"):
            st.markdown(item["prompt"])
        with st.chat_message("assistant"):
            st.markdown(item["response"])
            if item["files"]:
                st.caption("Artifacts")
                st.markdown(
                    " ".join(
                        f"<span class='file-pill ok-pill'>{path}</span>" if file_exists(path) else f"<span class='file-pill muted-pill'>{path}</span>"
                        for path in item["files"]
                    ),
                    unsafe_allow_html=True,
                )
            if item["logs"]:
                with st.expander("Console output"):
                    st.code(item["logs"])


def render_file_status(paths: list[str]) -> None:
    pills = []
    for path in paths:
        css_class = "ok-pill" if file_exists(path) else "muted-pill"
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


def render_sidebar() -> None:
    st.sidebar.markdown("## Genealogy Workspace")
    st.sidebar.caption("Gemini-style local research cockpit")
    st.sidebar.text_input("GEDCOM file", key="gedcom_path")
    st.sidebar.text_input("Scope / target", key="scope", placeholder="Entire tree or person name")
    st.sidebar.text_input("Default target name", key="target_name")
    st.sidebar.text_input("Document image", key="image_path")
    st.sidebar.text_input("Case name", key="case_name")

    st.sidebar.markdown("### Output status")
    for path in DEFAULT_OUTPUTS:
        marker = "●" if file_exists(path) else "○"
        st.sidebar.caption(f"{marker} {path}")

    st.sidebar.markdown("### Workspace tips")
    st.sidebar.caption("- Use Guided workflow first")
    st.sidebar.caption("- Review the Case Bundle tab after each run")
    st.sidebar.caption("- Person mappings appear once tree data exists")


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

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("People in scope", (tree_section.get("counts") or {}).get("people_in_scope", 0))
    col2.metric("Issues", (consistency_section.get("counts") or {}).get("issues_found", 0))
    col3.metric("Hints", (hints_section.get("counts") or {}).get("hints_generated", 0))
    col4.metric("Artifacts", len(bundle.get("artifacts") or []))

    st.markdown("#### Bundle context")
    st.write(
        {
            "generated_at": bundle.get("generated_at"),
            "input_file": bundle.get("input_file"),
            "scope": bundle.get("scope"),
            "available_sections": bundle.get("available_sections"),
        }
    )

    left, right = st.columns([1.2, 1])
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


render_sidebar()

st.markdown(
    """
    <div class="gem-hero">
        <h1 style="margin:0;">Genealogy Intelligence Workspace</h1>
        <p style="margin:0.45rem 0 0 0; color:#c7cbd3;">
            A desktop-style local app for running genealogy workflows, reviewing outputs, and exploring the active case bundle.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

status_col, feed_col = st.columns([0.9, 1.1])
with status_col:
    st.markdown("<div class='gem-card'>", unsafe_allow_html=True)
    st.markdown("### Active workspace")
    st.write(
        {
            "gedcom": st.session_state.gedcom_path,
            "scope": format_scope(st.session_state.scope),
            "default_target_name": st.session_state.target_name or "Not set",
            "document_image": st.session_state.image_path,
        }
    )
    st.markdown("#### Known outputs")
    render_file_status(DEFAULT_OUTPUTS)
    st.markdown("</div>", unsafe_allow_html=True)

with feed_col:
    render_activity_feed()


tab_dashboard, tab_guided, tab_tree, tab_research, tab_documents, tab_bundle = st.tabs(
    [
        "Dashboard",
        "Guided workflow",
        "Tree tools",
        "Research",
        "Documents & case assembly",
        "Case bundle",
    ]
)

with tab_dashboard:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Reports ready", sum(1 for path in DEFAULT_OUTPUTS if file_exists(path)))
    c2.metric("JSON exports", sum(1 for path in [TREE_JSON_FILE, CONSISTENCY_EXPORT_FILE, HINTS_EXPORT_FILE, CASE_BUNDLE_FILE] if file_exists(path)))
    bundle = read_json_file(CASE_BUNDLE_FILE) or {}
    c3.metric("Bundle artifacts", len(bundle.get("artifacts") or []))
    c4.metric("Mapped people", (bundle.get("person_artifact_counts") or {}).get("people_mapped", 0))

    preview_left, preview_right = st.columns(2)
    with preview_left:
        render_text_preview("Tree Structure Report", TREE_REPORT_FILE)
        render_text_preview("Consistency Report", CONSISTENCY_REPORT_FILE)
        render_text_preview("Research Hints Report", HINTS_REPORT_FILE)
    with preview_right:
        render_text_preview("Proof Summary Draft", PROOF_REPORT)
        render_text_preview("Evidence Index", EVIDENCE_INDEX_FILE)
        render_json_preview("Case Bundle Preview", CASE_BUNDLE_FILE)

with tab_guided:
    with st.form("guided-workflow-form"):
        st.markdown("Run the core sequence: tree analysis → consistency review → research hints.")
        guided_compile = st.checkbox("Compile proof summary after analysis", value=True)
        guided_evidence = st.checkbox("Refresh evidence locker after analysis", value=False)
        submitted = st.form_submit_button("Run guided workflow")
    if submitted:
        run_guided_workflow_ui(st.session_state.gedcom_path, st.session_state.scope, guided_compile, guided_evidence)
        st.rerun()

with tab_tree:
    left, right = st.columns(2)
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

with tab_research:
    left, right = st.columns(2)
    with left:
        with st.form("external-recon-form"):
            st.markdown("#### External archival search")
            external_target = st.text_input("Target name", value=st.session_state.target_name or st.session_state.scope)
            external_birth = st.text_input("Birth year", value=st.session_state.birth_year)
            external_death = st.text_input("Death year", value=st.session_state.death_year)
            external_place = st.text_input("Place", value=st.session_state.place)
            external_focus = st.text_input("Record focus", value=st.session_state.record_focus)
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

        render_text_preview("External recon report", EXTERNAL_RECON_REPORT_FILE)

    with right:
        with st.form("broad-recon-form"):
            st.markdown("#### Broad web recon")
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

        render_text_preview("Broad web recon report", BROAD_RECON_REPORT_FILE)

with tab_documents:
    left, right = st.columns(2)
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

with tab_bundle:
    render_bundle_explorer()
