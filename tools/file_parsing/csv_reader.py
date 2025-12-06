"""CSV parsing utility for APAS agents."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass(frozen=True)
class CSVReaderConfig:
    max_rows: int = 10000
    sniff_bytes: int = 2048


class CSVReader:
    """Reads CSV files and returns structured, JSON-serializable payloads."""

    def __init__(self, config: Optional[CSVReaderConfig] = None) -> None:
        self.config = config or CSVReaderConfig()

    def read(
        self,
        path: str,
        *,
        has_headers: bool = True,
        limit: Optional[int] = None,
        encoding: str = "utf-8",
        selected_columns: Optional[List[str]] = None,
    ) -> Dict[str, object]:
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        limit_rows = limit or self.config.max_rows
        rows: List[Dict[str, Optional[str]]] = []
        columns: List[str] = []

        with file_path.open("r", encoding=encoding, newline="") as handle:
            sample = handle.read(self.config.sniff_bytes)
            handle.seek(0)
            dialect = csv.Sniffer().sniff(sample) if has_headers else csv.excel
            handle.seek(0)

            if has_headers:
                reader = csv.DictReader(handle, dialect=dialect)
                columns = reader.fieldnames or []
                for idx, row in enumerate(reader):
                    if idx >= limit_rows:
                        break
                    record = {k: row.get(k) for k in (selected_columns or row.keys())}
                    rows.append(record)
            else:
                reader2 = csv.reader(handle, dialect=dialect)
                for idx, row in enumerate(reader2):
                    if idx >= limit_rows:
                        break
                    if not columns:
                        columns = [f"col_{i}" for i in range(len(row))]
                    record = {columns[i]: value for i, value in enumerate(row)}
                    rows.append(record)

        summary = self._summarize(rows)
        return {
            "path": str(file_path),
            "row_count": len(rows),
            "columns": selected_columns or columns,
            "rows": rows,
            "summary": summary,
        }

    @staticmethod
    def _summarize(rows: List[Dict[str, Optional[str]]]) -> Dict[str, Dict[str, object]]:
        summary: Dict[str, Dict[str, object]] = {}
        if not rows:
            return summary

        columns = rows[0].keys()
        for column in columns:
            values = [row[column] for row in rows if row.get(column)]
            unique_values = list({value for value in values})[:5]
            summary[column] = {
                "non_null": len(values),
                "sample_values": unique_values,
            }
        return summary


if __name__ == "__main__":
    sample_path = Path("/tmp/apas_sample.csv")
    sample_path.write_text("day,theme,cta\n1,Launch teaser,Join waitlist\n2,Behind the scenes,Subscribe", encoding="utf-8")
    reader = CSVReader()
    print(reader.read(str(sample_path)))
