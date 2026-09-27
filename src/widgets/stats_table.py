"""Stats table widget — DataTable wrapper for statistics display."""

from __future__ import annotations

from typing import Any

from textual.widgets import DataTable


def create_stats_table(
    columns: list[tuple[str, str]] | None = None,
    rows: list[list[str | float]] | None = None,
) -> DataTable[Any]:
    """Create a styled DataTable for statistics.

    Args:
        columns: List of (column_key, column_label) tuples.
        rows: List of row data lists.

    Returns:
        A configured DataTable widget.
    """
    table: DataTable[Any] = DataTable()
    table.show_header = True
    table.zebra_stripes = True
    table.show_cursor = False

    default_columns = [("metric", "Metric"), ("value", "Value")]

    for key, label in (columns or default_columns):
        table.add_column(label, key=key)

    for row in (rows or []):
        table.add_row(*[str(cell) for cell in row])

    return table
