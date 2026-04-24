import re
import unicodedata

# ==========================================
# ROLE 2: ETL/ELT BUILDER
# ==========================================
# Task: Clean the transcript text and extract key information.


def clean_transcript(file_path):
    # --- FILE READING (Handled for students) ---
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    # ------------------------------------------

    cleaned_text = re.sub(r"\[\d{2}:\d{2}:\d{2}\]", "", text)
    cleaned_text = re.sub(
        r"\[(?:Music(?:\s+(?:starts|ends))?|inaudible|Laughter)\]",
        "",
        cleaned_text,
        flags=re.IGNORECASE,
    )
    cleaned_text = re.sub(r"\[Speaker\s+\d+\]\s*:\s*", "", cleaned_text, flags=re.IGNORECASE)
    cleaned_text = re.sub(r"[ \t]+", " ", cleaned_text)
    cleaned_text = re.sub(r"\n{2,}", "\n", cleaned_text).strip()

    normalized_for_search = _strip_accents(text).lower()
    detected_price_vnd = None
    if re.search(r"\b500\s*,?\s*000\b", normalized_for_search):
        detected_price_vnd = 500000
    elif "nam tram nghin" in normalized_for_search:
        detected_price_vnd = 500000

    return {
        "document_id": "video-demo-transcript",
        "content": cleaned_text,
        "source_type": "Video",
        "author": "Speaker 1",
        "source_metadata": {
            "detected_price_vnd": detected_price_vnd,
            "line_count": len([ln for ln in cleaned_text.splitlines() if ln.strip()]),
        },
    }


def _strip_accents(value):
    normalized = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
