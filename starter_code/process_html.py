import re
import unicodedata
from bs4 import BeautifulSoup

# ==========================================
# ROLE 2: ETL/ELT BUILDER
# ==========================================
# Task: Extract product data from the HTML table, ignoring boilerplate.


def parse_html_catalog(file_path):
    # --- FILE READING (Handled for students) ---
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    # ------------------------------------------

    table = soup.find("table", id="main-catalog")
    if table is None:
        return []

    documents = []
    tbody = table.find("tbody")
    if tbody is None:
        return documents

    for row in tbody.find_all("tr"):
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        if len(cols) != 6:
            continue

        product_id, product_name, category, price_raw, stock_raw, rating_raw = cols
        parsed_price = _parse_price(price_raw)

        try:
            stock_value = int(stock_raw)
        except (TypeError, ValueError):
            stock_value = None

        if parsed_price is None:
            price_text = "price unavailable"
        else:
            price_text = f"{parsed_price:.0f} VND"

        content = (
            f"{product_name} in category {category}; {price_text}; "
            f"stock {stock_value if stock_value is not None else 'unknown'}; rating {rating_raw}."
        )

        documents.append(
            {
                "document_id": f"html-{product_id.lower()}",
                "content": content,
                "source_type": "HTML",
                "author": "VinShop Catalog",
                "source_metadata": {
                    "product_id": product_id,
                    "product_name": product_name,
                    "category": category,
                    "listed_price_vnd": parsed_price,
                    "stock_quantity": stock_value,
                    "rating_text": rating_raw,
                },
            }
        )

    return documents


def _strip_accents(value):
    normalized = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def _parse_price(raw_price):
    if raw_price is None:
        return None

    normalized = _strip_accents(raw_price).strip().lower()
    if normalized in {"n/a", "na", "lien he", "khong ro"}:
        return None

    digits = re.sub(r"[^\d\-]", "", raw_price)
    if not digits:
        return None

    try:
        return float(digits)
    except ValueError:
        return None
