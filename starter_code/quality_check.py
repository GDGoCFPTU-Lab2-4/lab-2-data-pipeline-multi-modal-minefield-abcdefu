import re

# ==========================================
# ROLE 3: OBSERVABILITY & QA ENGINEER
# ==========================================
# Task: Implement quality gates to reject corrupt data or logic discrepancies.

TOXIC_STRINGS = [
    "null pointer exception",
    "traceback (most recent call last)",
    "segmentation fault",
    "fatal error",
]


def run_quality_gate(document_dict):
    content = (document_dict or {}).get("content", "")
    if not isinstance(content, str):
        return False

    normalized_content = " ".join(content.split()).strip()

    # Reject extremely short content.
    if len(normalized_content) < 20:
        return False

    # Reject known toxic/error payloads.
    lowered_content = normalized_content.lower()
    if any(toxic_text in lowered_content for toxic_text in TOXIC_STRINGS):
        return False

    # Flag potential tax-rate discrepancy (8% vs 10%) without rejecting by default.
    quality_flags = []
    if re.search(r"\b8%\b", lowered_content) and re.search(r"\b10%\b", lowered_content):
        if "tax" in lowered_content or "vat" in lowered_content:
            quality_flags.append("Potential discrepancy: tax description references both 8% and 10%.")

    source_metadata = document_dict.setdefault("source_metadata", {})
    if isinstance(source_metadata, dict) and quality_flags:
        existing_flags = source_metadata.get("quality_flags", [])
        if not isinstance(existing_flags, list):
            existing_flags = [str(existing_flags)]
        source_metadata["quality_flags"] = existing_flags + quality_flags

    return True
