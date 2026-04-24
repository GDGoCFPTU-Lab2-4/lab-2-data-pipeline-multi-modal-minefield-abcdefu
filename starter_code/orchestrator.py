import json
import time
import os

# Robust path handling
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "raw_data")


# Import role-specific modules
from schema import UnifiedDocument
from process_pdf import extract_pdf_data
from process_transcript import clean_transcript
from process_html import parse_html_catalog
from process_csv import process_sales_csv
from process_legacy_code import extract_logic_from_code
from quality_check import run_quality_gate

# ==========================================
# ROLE 4: DEVOPS & INTEGRATION SPECIALIST
# ==========================================
# Task: Orchestrate the ingestion pipeline and handle errors/SLA.


def main():
    start_time = time.time()
    final_kb = []

    # --- FILE PATH SETUP (Handled for students) ---
    pdf_path = os.path.join(RAW_DATA_DIR, "lecture_notes.pdf")
    trans_path = os.path.join(RAW_DATA_DIR, "demo_transcript.txt")
    html_path = os.path.join(RAW_DATA_DIR, "product_catalog.html")
    csv_path = os.path.join(RAW_DATA_DIR, "sales_records.csv")
    code_path = os.path.join(RAW_DATA_DIR, "legacy_pipeline.py")

    output_path = os.path.join(os.path.dirname(SCRIPT_DIR), "processed_knowledge_base.json")
    # ----------------------------------------------

    processors = [
        ("PDF", lambda: extract_pdf_data(pdf_path)),
        ("Video", lambda: clean_transcript(trans_path)),
        ("HTML", lambda: parse_html_catalog(html_path)),
        ("CSV", lambda: process_sales_csv(csv_path)),
        ("Code", lambda: extract_logic_from_code(code_path)),
    ]

    for source_name, processor in processors:
        try:
            result = processor()
            for document in _as_document_list(result):
                if not run_quality_gate(document):
                    continue

                validated = UnifiedDocument(**document)
                final_kb.append(_model_dump(validated))
        except Exception as exc:
            print(f"[WARN] Failed processing {source_name}: {exc}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_kb, f, ensure_ascii=False, indent=2)

    end_time = time.time()
    print(f"Pipeline finished in {end_time - start_time:.2f} seconds.")
    print(f"Total valid documents stored: {len(final_kb)}")


def _as_document_list(result):
    if result is None:
        return []
    if isinstance(result, list):
        return [doc for doc in result if isinstance(doc, dict)]
    if isinstance(result, dict):
        return [result]
    return []


def _model_dump(model):
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    return json.loads(model.json())


if __name__ == "__main__":
    main()
