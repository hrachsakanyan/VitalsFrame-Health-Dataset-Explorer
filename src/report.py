"""Render the analysis results as a standalone Markdown report.

Kept separate from ``analysis.py`` so that the analysis functions stay pure
DataFrame-in / DataFrame-out and know nothing about formatting.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from . import analysis, config as cfg


def _table(df: pd.DataFrame) -> str:
    """Render a DataFrame as a GitHub-flavoured Markdown table.

    A MultiIndex is flattened into ordinary columns first — ``to_markdown``
    otherwise renders each row label as a Python tuple, e.g. ``('40-49',
    'male')``, which is unreadable in a report.
    """
    if df.index.nlevels > 1:
        # Promote the levels to real columns, then drop the 0..n counter that
        # reset_index leaves behind — it carries no information.
        return df.reset_index().to_markdown(index=False)
    return df.to_markdown()


def build_summary_report(df: pd.DataFrame) -> str:
    """Assemble the full report as a Markdown string."""
    n_rows, n_cols = df.shape
    measured = df[cfg.COLUMNS]
    missing_cells = int(measured.isna().sum().sum())
    total_cells = measured.size
    disease_rate = df["has_disease"].mean() * 100

    parts: list[str] = []
    add = parts.append

    add("# VitalsFrame — Summary Statistics Report")
    add("")
    add(f"*Generated {date.today().isoformat()} from the UCI Heart Disease databases.*")
    add("")
    add("## Dataset at a glance")
    add("")
    add(f"- **Patients:** {n_rows:,}")
    add(f"- **Columns:** {n_cols} ({len(cfg.COLUMNS)} source attributes + derived and metadata)")
    add(f"- **Contributing institutions:** {df['institution'].nunique()}")
    add(f"- **Overall disease prevalence:** {disease_rate:.1f}%")
    add(f"- **Missing measured values:** {missing_cells:,} of {total_cells:,} "
        f"({missing_cells / total_cells * 100:.1f}%)")
    add("")

    add("## Missing data")
    add("")
    add("Percentage missing per column, by source database. The gaps are not random — "
        "they cluster almost entirely by institution, which is why any pooled analysis "
        "of `ca`, `thal` or `slope` is effectively an analysis of Cleveland.")
    add("")
    add(_table(analysis.missing_by_site(df)))
    add("")

    add("## Numeric distributions")
    add("")
    add(_table(df[analysis.FLOAT_COLUMNS].describe().T.round(1)))
    add("")

    add("## Questions explored")
    add("")
    for title, table in analysis.answer_all(df).items():
        add(f"### {title}")
        add("")
        add(_table(table))
        add("")

    add("## Data dictionary")
    add("")
    add(_table(analysis.data_dictionary()))
    add("")

    return "\n".join(parts)


def write_summary_report(df: pd.DataFrame, report_dir: Path | None = None) -> Path:
    """Write the Markdown report to ``reports/`` and return its path."""
    report_dir = Path(report_dir) if report_dir is not None else cfg.REPORT_DIR
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / cfg.SUMMARY_REPORT
    path.write_text(build_summary_report(df), encoding="utf-8")
    return path
