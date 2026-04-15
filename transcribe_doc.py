from __future__ import annotations

import base64
from pathlib import Path

from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

from report_utils import write_report

REPORT_FILE = "Transcription_Report.txt"


def transcribe_document(image_path: str = "document.jpg") -> str | None:
    print(f"\n[+] Initializing vision workflow for: {image_path}")

    try:
        image_data = base64.b64encode(Path(image_path).read_bytes()).decode("utf-8")
    except FileNotFoundError:
        print(f"[-] ERROR: '{image_path}' not found.")
        return None

    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": (
                    "You are an expert historical archivist. Transcribe the handwriting in this document exactly as written, "
                    "line by line. If a word is illegible, write [illegible]. Preserve original spelling and avoid repetition."
                ),
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
            },
        ]
    )

    try:
        llm = ChatOllama(model="llama3.2-vision", temperature=0.2)
        response = llm.invoke([message]).content.strip()
    except Exception as exc:
        print(f"[-] CRITICAL ERROR: {exc}")
        return None

    write_report(
        REPORT_FILE,
        "Transcription Report",
        image_path,
        image_path,
        [("Transcription", response)],
        confidence_notes=[
            "Review unclear handwriting against the original image before citing the transcription.",
        ],
        next_steps=[
            "Attach the transcription to the evidence locker if it contributes to the active case.",
        ],
    )
    print(response)
    print(f"\n[+] Transcription complete. Report written to {REPORT_FILE}")
    return REPORT_FILE


def main() -> None:
    image_path = input("Image file path [document.jpg]: ").strip() or "document.jpg"
    transcribe_document(image_path)


if __name__ == "__main__":
    main()
