"""VitalsFrame — loading, cleaning and analysing the UCI Heart Disease data.

The module is organised as the pipeline actually runs:

    load  ->  inspect  ->  clean  ->  analyse  ->  export

Every function takes a DataFrame and returns a new one; nothing is mutated in
place. That makes the functions safe to call in any order from a notebook, which
is how they are used in ``notebooks/exploration.ipynb``.

Run the whole pipeline from the command line with::

    python -m src.analysis

"""

from __future__ import annotations

import argparse
import io
from pathlib import Path

import pandas as pd

from . import config as cfg

# Columns that are integer codes rather than measurements. Reading them as a
# nullable integer type keeps "1" from printing as "1.0" everywhere and makes
# the code -> label lookups in `decode_categoricals` exact.
INT_CODE_COLUMNS = ["sex", "cp", "fbs", "restecg", "exang", "slope", "ca", "thal", "num"]

FLOAT_COLUMNS = ["age", "trestbps", "chol", "thalach", "oldpeak"]


# ==========================================================================
# 1. Load
# ==========================================================================


def load_site(site: str, raw_dir: Path | None = None) -> pd.DataFrame:
    """Read one of the four source databases into a DataFrame.

    The ``processed.*`` files are headerless CSVs using ``?`` for missing
    values, so both have to be declared up front.
    """
    if site not in cfg.RAW_FILES:
        raise KeyError(f"Unknown site {site!r}. Expected one of {sorted(cfg.RAW_FILES)}.")

    raw_dir = Path(raw_dir) if raw_dir is not None else cfg.RAW_DIR
    path = raw_dir / cfg.RAW_FILES[site]
    if not path.exists():
        raise FileNotFoundError(
            f"Missing raw data file: {path}\n"
            "Download it first with:  python -m src.fetch_data"
        )

    df = pd.read_csv(
        path,
        header=None,
        names=cfg.COLUMNS,
        na_values=cfg.NA_VALUES,
        skipinitialspace=True,
    )
    df.insert(0, "site", site)
    return df


def load_all(raw_dir: Path | None = None) -> pd.DataFrame:
    """Stack all four databases into one DataFrame, tagged by ``site``.

    They share an identical column layout, so this is a straight concatenation.
    ``ignore_index=True`` gives the combined frame a clean 0..n-1 index instead
    of four overlapping ones.
    """
    frames = [load_site(site, raw_dir=raw_dir) for site in cfg.RAW_FILES]
    return pd.concat(frames, ignore_index=True)


def coerce_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Give every column its proper dtype.

    Because ``?`` becomes NaN, pandas reads even the pure code columns as
    float64. ``Int64`` (capital I) is the nullable integer type: it holds whole
    numbers *and* missing values, which plain int64 cannot.
    """
    df = df.copy()
    for col in FLOAT_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in INT_CODE_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    return df


# ==========================================================================
# 2. Inspect
# ==========================================================================


def describe_frame(df: pd.DataFrame) -> str:
    """Return ``df.info()`` as a string.

    ``DataFrame.info`` prints to stdout and returns None, so it cannot be put in
    a report or a notebook variable directly — redirecting it into a buffer is
    the standard way around that.
    """
    buffer = io.StringIO()
    df.info(buf=buffer)
    return buffer.getvalue()


def inspect(df: pd.DataFrame, name: str = "dataset") -> None:
    """Print the standard first-look summary: shape, head, info, describe."""
    print(f"=== {name} ===")
    print(f"shape: {df.shape[0]:,} rows x {df.shape[1]} columns\n")
    print("--- head ---")
    print(df.head())
    print("\n--- info ---")
    print(describe_frame(df))
    print("--- describe ---")
    print(df.describe().T)


def missing_report(df: pd.DataFrame) -> pd.DataFrame:
    """Count missing values per column, most-missing first.

    Returns a DataFrame rather than printing, so it can be sorted, filtered or
    written into the summary report.
    """
    missing = df.isna().sum()
    report = pd.DataFrame(
        {
            "missing": missing,
            "missing_pct": (missing / len(df) * 100).round(1),
            "dtype": df.dtypes.astype(str),
        }
    )
    return report.sort_values("missing", ascending=False)


def missing_by_site(df: pd.DataFrame) -> pd.DataFrame:
    """Percentage of missing values per column, broken out by source database.

    This is the single most useful table in the project: it shows that the
    columns are not missing at random but almost entirely by institution.
    """
    per_site = df.groupby("site")[cfg.COLUMNS].apply(
        lambda block: block.isna().mean() * 100
    )
    return per_site.round(1)


def data_dictionary() -> pd.DataFrame:
    """The column reference table, as a DataFrame."""
    return pd.DataFrame(
        {"column": cfg.COLUMNS, "description": [cfg.COLUMN_DESCRIPTIONS[c] for c in cfg.COLUMNS]}
    ).set_index("column")


# ==========================================================================
# 3. Clean
# ==========================================================================


def flag_sentinel_zeros(df: pd.DataFrame) -> pd.DataFrame:
    """Convert impossible zeros into real missing values.

    A serum cholesterol or resting blood pressure of 0 mg/dl is not a low
    reading, it is an unrecorded one. Left as 0 it silently pulls every mean
    down — the Switzerland database stores nearly all of its cholesterol values
    this way.
    """
    df = df.copy()
    for col in cfg.ZERO_AS_MISSING:
        # `mask` rather than `replace(0, NA)`: replace would promote the column
        # to object dtype, and later numeric steps (pd.cut) cannot work with it.
        df[col] = df[col].mask(df[col] == 0)
    return df


def enforce_ranges(df: pd.DataFrame) -> pd.DataFrame:
    """Blank out values outside the physiologically plausible range.

    The bounds in ``config.PLAUSIBLE_RANGES`` are wide on purpose: the goal is
    to catch data-entry errors, not to quietly delete genuine outliers.
    """
    df = df.copy()
    for col, (low, high) in cfg.PLAUSIBLE_RANGES.items():
        outside = (df[col] < low) | (df[col] > high)
        df[col] = df[col].where(~outside.fillna(False))
    return df


def drop_incomplete(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows missing a column that no analysis here can work without."""
    return df.dropna(subset=cfg.REQUIRED_COLUMNS).reset_index(drop=True)


def decode_categoricals(df: pd.DataFrame) -> pd.DataFrame:
    """Add human-readable label columns alongside the numeric codes.

    The codes are kept — they are what the original papers use — but every
    grouping and every chart in this project keys off the labels, so a summary
    table reads "male / female" instead of "1 / 0".
    """
    df = df.copy()
    for source, (target, mapping) in cfg.LABEL_MAPS.items():
        df[target] = df[source].map(mapping)
    return df


def add_derived(df: pd.DataFrame) -> pd.DataFrame:
    """Add the derived columns the domain questions are asked in terms of.

    ``has_disease`` collapses the 0-4 severity scale to a binary. That matches
    the original study, which treated 0 as "less than 50% diameter narrowing"
    and everything above it as significant coronary artery disease.
    """
    df = df.copy()

    df["age_group"] = pd.cut(
        df["age"],
        bins=cfg.AGE_BIN_EDGES,
        labels=cfg.AGE_BIN_LABELS,
        right=False,  # 40 belongs to "40-49", not "<40"
    )
    df["chol_group"] = pd.cut(
        df["chol"], bins=cfg.CHOL_BIN_EDGES, labels=cfg.CHOL_BIN_LABELS, right=False
    )
    df["bp_group"] = pd.cut(
        df["trestbps"], bins=cfg.BP_BIN_EDGES, labels=cfg.BP_BIN_LABELS, right=False
    )

    df["has_disease"] = (df["num"] > 0).astype("boolean")
    df["disease_label"] = df["has_disease"].map({True: "disease", False: "no disease"})

    return df


def attach_site_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """Left-join the institution lookup table onto the patient rows.

    A left join (rather than inner) is deliberate: if a site key ever failed to
    match, the patients would survive with null metadata and the problem would
    be visible, instead of the rows silently disappearing.
    """
    sites = pd.DataFrame(cfg.SITE_METADATA)
    merged = df.merge(sites, on="site", how="left", validate="many_to_one")

    unmatched = merged["institution"].isna().sum()
    if unmatched:
        raise ValueError(f"{unmatched} rows had a site with no metadata entry.")
    return merged


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Run the full cleaning pipeline.

    ``DataFrame.pipe`` chains the steps left to right so the order of operations
    is readable top-to-bottom, and each step stays independently testable.
    """
    return (
        df.pipe(coerce_dtypes)
        .pipe(flag_sentinel_zeros)
        .pipe(enforce_ranges)
        .pipe(drop_incomplete)
        .pipe(decode_categoricals)
        .pipe(add_derived)
        .pipe(attach_site_metadata)
    )


def impute_missing(df: pd.DataFrame, group_by: str = "site") -> pd.DataFrame:
    """Fill remaining gaps using within-group statistics.

    Imputing within ``site`` rather than across the whole pooled dataset matters
    here: the four institutions have visibly different patient populations, so a
    global median would import Cleveland's profile into Switzerland's rows.

    Numeric columns get the group median (resistant to outliers); code columns
    get the group mode (a median of a category code would be meaningless).
    Anything still missing afterwards — a group where the column is *entirely*
    absent — falls back to the dataset-wide statistic.
    """
    df = df.copy()

    for col in FLOAT_COLUMNS:
        group_median = df.groupby(group_by)[col].transform("median")
        df[col] = df[col].fillna(group_median).fillna(df[col].median())

    for col in INT_CODE_COLUMNS:
        modes = df.groupby(group_by)[col].transform(_first_mode)
        overall = _first_mode(df[col])
        df[col] = df[col].fillna(modes).fillna(overall)

    # The derived columns were built from pre-imputation values, so rebuild them
    # rather than leaving age_group / chol_group stale.
    return df.pipe(decode_categoricals).pipe(add_derived)


def _first_mode(series: pd.Series):
    """Most frequent value in a series, or NA if there is nothing to count."""
    modes = series.mode(dropna=True)
    return modes.iloc[0] if not modes.empty else pd.NA


# ==========================================================================
# 4. Filter
# ==========================================================================


def filter_patients(
    df: pd.DataFrame,
    *,
    site: str | list[str] | None = None,
    sex: str | None = None,
    min_age: float | None = None,
    max_age: float | None = None,
    has_disease: bool | None = None,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    """Select a subset of rows and columns using boolean masks.

    Each argument left as None is simply skipped, so callers only state the
    conditions they care about::

        filter_patients(df, sex="female", min_age=60, has_disease=True)
    """
    mask = pd.Series(True, index=df.index)

    if site is not None:
        wanted = [site] if isinstance(site, str) else site
        mask &= df["site"].isin(wanted)
    if sex is not None:
        mask &= df["sex_label"] == sex
    if min_age is not None:
        mask &= df["age"] >= min_age
    if max_age is not None:
        mask &= df["age"] <= max_age
    if has_disease is not None:
        mask &= df["has_disease"] == has_disease

    subset = df.loc[mask]
    if columns is not None:
        subset = subset[columns]
    return subset.reset_index(drop=True)


# ==========================================================================
# 5. Analyse — one function per domain question
# ==========================================================================


def mean_cholesterol_by_age_group(df: pd.DataFrame) -> pd.DataFrame:
    """Q1. How does serum cholesterol vary across age bands?

    ``n_measured`` is reported next to the mean on purpose. Cholesterol is the
    most heavily missing vital in this dataset, so a mean without its sample
    size is not interpretable.
    """
    grouped = df.groupby("age_group", observed=True)["chol"].agg(
        n_measured="count", mean="mean", median="median", std="std"
    )
    grouped["n_patients"] = df.groupby("age_group", observed=True).size()
    return grouped.round(1)


def disease_rate_by(df: pd.DataFrame, *keys: str) -> pd.DataFrame:
    """Q2. Disease prevalence within any grouping.

    Called with one or more column names::

        disease_rate_by(df, "age_group")
        disease_rate_by(df, "age_group", "sex_label")

    ``mean`` of a boolean column is the proportion that is True, which is what
    makes the prevalence calculation a one-liner.
    """
    keys = keys or ("age_group",)
    grouped = df.groupby(list(keys), observed=True)["has_disease"].agg(
        n_patients="size", n_with_disease="sum", disease_rate="mean"
    )
    grouped["disease_rate_pct"] = (grouped["disease_rate"] * 100).round(1)
    return grouped.drop(columns="disease_rate")


def vitals_by_disease_status(df: pd.DataFrame) -> pd.DataFrame:
    """Q3. Do the measured vitals differ between diagnosed and healthy patients?

    A multi-column aggregation: the same set of statistics applied to every
    vital, then transposed so each vital is a row.
    """
    vitals = ["age", "trestbps", "chol", "thalach", "oldpeak"]
    summary = df.groupby("disease_label", observed=True)[vitals].agg(["mean", "median", "count"])
    return summary.T.round(1).rename_axis(index=["vital", "statistic"])


def chest_pain_vs_disease(df: pd.DataFrame) -> pd.DataFrame:
    """Q4. Which presenting chest-pain type carries the highest disease rate?

    The clinically counter-intuitive answer — asymptomatic patients have the
    highest rate — is a selection effect worth stating plainly: these people
    were referred for angiography for some other reason.
    """
    result = disease_rate_by(df, "cp_label")
    return result.sort_values("disease_rate_pct", ascending=False)


def heart_rate_by_age_and_disease(df: pd.DataFrame) -> pd.DataFrame:
    """Q5. Maximum achieved heart rate by age band and diagnosis (pivot table).

    ``pivot_table`` is the right tool when the question has two grouping axes
    and you want them laid out as rows and columns rather than a stacked index.
    """
    return pd.pivot_table(
        df,
        values="thalach",
        index="age_group",
        columns="disease_label",
        aggfunc="mean",
        observed=True,
    ).round(1)


def cholesterol_pivot(df: pd.DataFrame) -> pd.DataFrame:
    """Q1b. Mean cholesterol as an age-group x sex pivot table."""
    return pd.pivot_table(
        df,
        values="chol",
        index="age_group",
        columns="sex_label",
        aggfunc="mean",
        observed=True,
    ).round(1)


def site_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Q6. How do the four contributing institutions compare?

    Named aggregation (``agg(name=(column, func))``) is used here because the
    output columns come from different source columns — a plain ``agg`` on a
    single column could not produce this table.
    """
    profile = df.groupby("institution", observed=True).agg(
        n_patients=("age", "size"),
        mean_age=("age", "mean"),
        pct_male=("sex", "mean"),
        mean_chol=("chol", "mean"),
        chol_measured=("chol", "count"),
        disease_rate=("has_disease", "mean"),
    )
    profile["pct_male"] = (profile["pct_male"] * 100).round(1)
    profile["disease_rate_pct"] = (profile.pop("disease_rate") * 100).round(1)
    profile["chol_coverage_pct"] = (profile["chol_measured"] / profile["n_patients"] * 100).round(1)
    return profile.round(1)


def severity_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Cross-tabulation of diagnosis severity (0-4) against source database."""
    table = pd.crosstab(df["institution"], df["num"], margins=True, margins_name="All")
    table.columns.name = "severity"
    return table


def answer_all(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Run every domain question and return the results keyed by title."""
    return {
        "Q1. Mean cholesterol by age group": mean_cholesterol_by_age_group(df),
        "Q1b. Mean cholesterol by age group and sex": cholesterol_pivot(df),
        "Q2. Disease rate by age group and sex": disease_rate_by(df, "age_group", "sex_label"),
        "Q3. Vitals by disease status": vitals_by_disease_status(df),
        "Q4. Disease rate by chest pain type": chest_pain_vs_disease(df),
        "Q5. Max heart rate by age group and diagnosis": heart_rate_by_age_and_disease(df),
        "Q6. Profile of the four contributing institutions": site_profile(df),
        "Q7. Diagnosis severity by institution": severity_distribution(df),
    }


# ==========================================================================
# 6. Export
# ==========================================================================


def export_clean(df: pd.DataFrame, filename: str, clean_dir: Path | None = None) -> Path:
    """Write a cleaned DataFrame to ``data/clean/``.

    ``index=False`` because the index here is a meaningless row counter — saving
    it would add a stray unnamed column on the next read.
    """
    clean_dir = Path(clean_dir) if clean_dir is not None else cfg.CLEAN_DIR
    clean_dir.mkdir(parents=True, exist_ok=True)
    path = clean_dir / filename
    df.to_csv(path, index=False)
    return path


# ==========================================================================
# CLI
# ==========================================================================


def run_pipeline(raw_dir: Path | None = None, clean_dir: Path | None = None,
                 report_dir: Path | None = None, write_report: bool = True) -> pd.DataFrame:
    """Load -> clean -> export -> report, printing progress as it goes."""
    from .report import write_summary_report  # imported here to keep the module import light

    print("Loading four source databases ...")
    raw = load_all(raw_dir=raw_dir)
    print(f"  loaded {len(raw):,} raw patient records")

    print("Cleaning ...")
    df = clean(raw)
    dropped = len(raw) - len(df)
    print(f"  {len(df):,} records retained ({dropped} dropped for missing key fields)")

    total_cells = len(df) * len(cfg.COLUMNS)
    missing_cells = int(df[cfg.COLUMNS].isna().sum().sum())
    print(f"  {missing_cells:,} / {total_cells:,} measured values missing "
          f"({missing_cells / total_cells * 100:.1f}%)")

    clean_path = export_clean(df, cfg.CLEAN_CSV, clean_dir)
    print(f"Wrote {clean_path}")

    imputed = impute_missing(df)
    imputed_path = export_clean(imputed, cfg.IMPUTED_CSV, clean_dir)
    print(f"Wrote {imputed_path}")

    if write_report:
        report_path = write_summary_report(df, report_dir=report_dir)
        print(f"Wrote {report_path}")

    return df


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m src.analysis",
        description="Clean the UCI Heart Disease data and answer the project's domain questions.",
    )
    parser.add_argument("--raw-dir", type=Path, default=None, help="override data/raw")
    parser.add_argument("--clean-dir", type=Path, default=None, help="override data/clean")
    parser.add_argument("--report-dir", type=Path, default=None, help="override reports/")
    parser.add_argument("--no-report", action="store_true", help="skip the markdown report")
    parser.add_argument("--show", action="store_true", help="print every answer table to stdout")
    args = parser.parse_args(argv)

    df = run_pipeline(
        raw_dir=args.raw_dir,
        clean_dir=args.clean_dir,
        report_dir=args.report_dir,
        write_report=not args.no_report,
    )

    if args.show:
        for title, table in answer_all(df).items():
            print(f"\n=== {title} ===")
            print(table)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
