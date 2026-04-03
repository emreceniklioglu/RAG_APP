"""Tabular file parsing service (CSV / Excel).

Reads CSV and XLSX files with pandas, converts each row to a
pipe-delimited string suitable for embedding.
"""

from pathlib import Path

import pandas as pd

from app.core.logging import logger
from app.utils.timers import log_timer


def parse_tabular(file_path: Path, filename: str) -> list[str]:
    """Parse a CSV or Excel file and convert rows to text chunks.

    Each row becomes a string in the format:
      "ColA: valA | ColB: valB | ColC: valC"
    NaN / None values are skipped.

    Args:
        file_path: Path to the saved file.
        filename: Original filename (used for extension detection).

    Returns:
        List of row-strings (one per row).

    Raises:
        ValueError: If the file is empty or has no usable rows.
    """
    ext = Path(filename).suffix.lower()

    with log_timer(f"Tabular parsing: {filename}"):
        if ext == ".csv":
            df = pd.read_csv(file_path, dtype=str)
        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(file_path, dtype=str, engine="openpyxl")
        else:
            raise ValueError(f"Desteklenmeyen tablo dosyası formatı: {ext}")

        if df.empty:
            raise ValueError(
                f"Dosya boş veya okunabilir satır içermiyor: {filename}"
            )

        row_strings: list[str] = []
        for idx, row in df.iterrows():
            parts: list[str] = []
            for col in df.columns:
                val = row[col]
                if pd.notna(val) and str(val).strip():
                    parts.append(f"{col}: {str(val).strip()}")
            if parts:
                row_strings.append(" | ".join(parts))

        if not row_strings:
            raise ValueError(
                f"Dosyada kullanılabilir veri satırı bulunamadı: {filename}"
            )

        logger.info(
            "Parsed %d rows from %s (%d columns)",
            len(row_strings), filename, len(df.columns),
        )
        return row_strings
