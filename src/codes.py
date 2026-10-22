"""Stock code helpers and name map for first-version single-stock flow."""

from __future__ import annotations

NAME_TO_CODE = {
    "宁德时代": "300750",
    "catl": "300750",
}


def resolve_code(query: str) -> tuple[str, str]:
    """Return (6-digit code, display name)."""
    q = query.strip()
    key = q.lower()
    if key in NAME_TO_CODE:
        code = NAME_TO_CODE[key]
        return code, q
    digits = "".join(ch for ch in q if ch.isdigit())
    if len(digits) == 6:
        return digits, q
    if q in NAME_TO_CODE:
        return NAME_TO_CODE[q], q
    raise ValueError(f"无法识别股票: {query}（第一版可用名称如「宁德时代」或代码 300750）")


def to_baostock(code: str) -> str:
    digits = "".join(ch for ch in code if ch.isdigit())
    if digits.startswith(("5", "6", "9")):
        return f"sh.{digits}"
    if digits.startswith(("4", "8")):
        return f"bj.{digits}"
    return f"sz.{digits}"
