import json
import os
import re
import time
from pathlib import Path
import google.generativeai as genai

# ==========================================
# ROLE 2: ETL/ELT BUILDER
# ==========================================
# Task: Use Gemini API to extract structured data from lecture_notes.pdf

GEMINI_MODEL_NAME = "gemini-1.5-flash"
MAX_RETRIES = 4


def extract_pdf_data(file_path):
    # --- FILE CHECK (Handled for students) ---
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return None
    # ------------------------------------------

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return _fallback_pdf_document(file_path, "GEMINI_API_KEY_not_set")

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        pdf_file = genai.upload_file(path=file_path)
        prompt = (
            "Extract title, author, and a concise summary from this PDF. "
            "Return JSON only with keys: title, author, summary."
        )
        response = _generate_with_backoff(model, [pdf_file, prompt])
        parsed = _parse_json_from_response(getattr(response, "text", "") or "")

        title = (parsed.get("title") or Path(file_path).stem).strip()
        author = (parsed.get("author") or "Unknown").strip()
        summary = (parsed.get("summary") or "").strip()
        if len(summary) < 20:
            summary = f"Summary unavailable from model response for {Path(file_path).name}."

        return {
            "document_id": f"pdf-{Path(file_path).stem}",
            "content": summary,
            "source_type": "PDF",
            "author": author,
            "source_metadata": {
                "title": title,
                "extraction_method": "gemini_api",
                "model": GEMINI_MODEL_NAME,
            },
        }
    except Exception as exc:
        print(f"Warning: Gemini extraction failed, using fallback. Reason: {exc}")
        return _fallback_pdf_document(file_path, str(exc))


def _generate_with_backoff(model, parts):
    delay_seconds = 1.0
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return model.generate_content(parts)
        except Exception as exc:
            error_text = str(exc).lower()
            retryable = "429" in error_text or "resource exhausted" in error_text
            if not retryable or attempt == MAX_RETRIES:
                raise
            time.sleep(delay_seconds)
            delay_seconds *= 2


def _parse_json_from_response(response_text):
    if not response_text:
        return {}

    cleaned = response_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.DOTALL).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if not match:
        return {}

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}


def _fallback_pdf_document(file_path, reason):
    file_name = Path(file_path).name
    return {
        "document_id": f"pdf-{Path(file_path).stem}",
        "content": (
            f"Fallback PDF extraction for {file_name}. "
            "Gemini output was unavailable, so only file-level metadata was captured."
        ),
        "source_type": "PDF",
        "author": "Unknown",
        "source_metadata": {
            "title": Path(file_path).stem.replace("_", " ").title(),
            "extraction_method": "fallback",
            "reason": reason,
        },
    }
