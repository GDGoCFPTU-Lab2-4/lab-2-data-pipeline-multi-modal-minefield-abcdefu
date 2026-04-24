import ast
import re

# ==========================================
# ROLE 2: ETL/ELT BUILDER
# ==========================================
# Task: Extract docstrings and comments from legacy Python code.


def extract_logic_from_code(file_path):
    # --- FILE READING (Handled for students) ---
    with open(file_path, "r", encoding="utf-8") as f:
        source_code = f.read()
    # ------------------------------------------

    tree = ast.parse(source_code)
    module_docstring = ast.get_docstring(tree) or ""

    function_docs = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            func_doc = ast.get_docstring(node)
            if func_doc:
                function_docs.append(f"{node.name}: {func_doc.strip()}")

    business_rule_ids = sorted(set(re.findall(r"Business Logic Rule\s*(\d+)", source_code, flags=re.IGNORECASE)))
    potential_tax_discrepancy = _detect_tax_discrepancy(source_code)

    content_parts = []
    if module_docstring:
        content_parts.append(module_docstring.strip())
    if function_docs:
        content_parts.extend(function_docs)
    content = "\n\n".join(content_parts).strip()

    return {
        "document_id": "code-legacy-pipeline",
        "content": content,
        "source_type": "Code",
        "author": "Senior Dev (retired)",
        "source_metadata": {
            "function_count": len([n for n in tree.body if isinstance(n, ast.FunctionDef)]),
            "business_rule_ids": business_rule_ids,
            "potential_tax_discrepancy": potential_tax_discrepancy,
        },
    }


def _detect_tax_discrepancy(source_code):
    tax_func_match = re.search(
        r"def\s+legacy_tax_calc\s*\(.*?\):(?P<body>.*?)(?=^\s*def\s+\w+\s*\(|\Z)",
        source_code,
        flags=re.DOTALL | re.MULTILINE,
    )
    if not tax_func_match:
        return False

    func_block = tax_func_match.group("body")
    comment_percents = [int(v) for v in re.findall(r"(\d+)\s*%", func_block)]
    rate_match = re.search(r"tax_rate\s*=\s*([0-9]*\.?[0-9]+)", func_block)

    if not comment_percents or not rate_match:
        return False

    code_percent = float(rate_match.group(1)) * 100
    return all(abs(comment_percent - code_percent) > 0.01 for comment_percent in comment_percents)
