import re
import unicodedata
from datetime import datetime
import pandas as pd

# ==========================================
# ROLE 2: ETL/ELT BUILDER
# ==========================================
# Task: Process sales records, handling type traps and duplicates.


def process_sales_csv(file_path):
    # --- FILE READING (Handled for students) ---
    df = pd.read_csv(file_path)
    # ------------------------------------------

    df = df.drop_duplicates(subset="id", keep="first").copy()
    df["clean_price"] = df["price"].apply(_parse_price)
    df["normalized_sale_date"] = df["date_of_sale"].apply(_normalize_date)
    df["stock_quantity"] = pd.to_numeric(df["stock_quantity"], errors="coerce")

    documents = []
    for _, row in df.iterrows():
        row_id = int(row["id"])
        clean_price = row["clean_price"]

        if clean_price is None:
            price_text = "price unavailable"
        else:
            price_text = f"{clean_price:.2f} {row['currency']}"

        content = (
            f"Sale record for {row['product_name']} ({row['category']}), "
            f"price {price_text}, sold on {row['normalized_sale_date']}."
        )

        documents.append(
            {
                "document_id": f"csv-{row_id}",
                "content": content,
                "source_type": "CSV",
                "author": row.get("seller_id", "Unknown"),
                "source_metadata": {
                    "sale_id": row_id,
                    "product_name": row["product_name"],
                    "category": row["category"],
                    "price": clean_price,
                    "currency": row["currency"],
                    "date_of_sale": row["normalized_sale_date"],
                    "seller_id": row.get("seller_id"),
                    "stock_quantity": None if pd.isna(row["stock_quantity"]) else int(row["stock_quantity"]),
                },
            }
        )

    return documents


def _strip_accents(value):
    normalized = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def _parse_price(value):
    if pd.isna(value):
        return None

    text = str(value).strip()
    normalized = _strip_accents(text).lower()
    if normalized in {"", "n/a", "na", "null", "none", "lien he"}:
        return None

    # Handle simple worded prices like "five dollars".
    if re.fullmatch(r"[a-z\s\-]+", normalized):
        word_to_number = {
            "zero": 0,
            "one": 1,
            "two": 2,
            "three": 3,
            "four": 4,
            "five": 5,
            "six": 6,
            "seven": 7,
            "eight": 8,
            "nine": 9,
            "ten": 10,
        }
        for word, number in word_to_number.items():
            if re.search(rf"\b{word}\b", normalized):
                return float(number)
        return None

    cleaned = text.replace(",", "")
    cleaned = re.sub(r"[^\d.\-]", "", cleaned)
    if cleaned in {"", "-", ".", "-."}:
        return None

    try:
        return float(cleaned)
    except ValueError:
        return None


def _normalize_date(value):
    if pd.isna(value):
        return None

    text = str(value).strip()
    text = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", text, flags=re.IGNORECASE)

    explicit_formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
        "%d %b %Y",
        "%B %d %Y",
    ]
    for date_format in explicit_formats:
        try:
            return datetime.strptime(text, date_format).strftime("%Y-%m-%d")
        except ValueError:
            continue

    parsed = pd.to_datetime(text, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.strftime("%Y-%m-%d")
