"""Data dictionary and paths for the UCI Heart Disease databases.

Everything that describes *the data* lives here — column names, the meaning of
each numeric code, physiological plausibility ranges, and where files live on
disk. Keeping it out of ``analysis.py`` means the analysis code reads like
analysis instead of a wall of dictionaries.

Source: Detrano, R. et al., UCI Machine Learning Repository, "Heart Disease"
(1988). See README.md for the full citation and publication request.
"""

from __future__ import annotations

from pathlib import Path

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLEAN_DIR = PROJECT_ROOT / "data" / "clean"
REPORT_DIR = PROJECT_ROOT / "reports"

# --------------------------------------------------------------------------
# The four source databases
# --------------------------------------------------------------------------
# The UCI archive ships 76 raw attributes per patient, but only 14 were used in
# the original study and only those 14 are released in the `processed.*` files.

RAW_FILES = {
    "cleveland": "processed.cleveland.data",
    "hungary": "processed.hungarian.data",
    "switzerland": "processed.switzerland.data",
    "long_beach": "processed.va.data",
}

# Collecting institution for each database. This is a genuine lookup table:
# it is merged onto the patient rows in `analysis.attach_site_metadata`.
SITE_METADATA = [
    {
        "site": "cleveland",
        "institution": "Cleveland Clinic Foundation",
        "city": "Cleveland",
        "country": "USA",
        "principal_investigator": "Robert Detrano, M.D., Ph.D.",
    },
    {
        "site": "hungary",
        "institution": "Hungarian Institute of Cardiology",
        "city": "Budapest",
        "country": "Hungary",
        "principal_investigator": "Andras Janosi, M.D.",
    },
    {
        "site": "switzerland",
        "institution": "University Hospitals Zurich & Basel",
        "city": "Zurich / Basel",
        "country": "Switzerland",
        "principal_investigator": "William Steinbrunn, M.D.; Matthias Pfisterer, M.D.",
    },
    {
        "site": "long_beach",
        "institution": "V.A. Medical Center",
        "city": "Long Beach, CA",
        "country": "USA",
        "principal_investigator": "Robert Detrano, M.D., Ph.D.",
    },
]

# --------------------------------------------------------------------------
# Column schema
# --------------------------------------------------------------------------
# The processed files have no header row; columns are positional, in this order.

COLUMNS = [
    "age",       # age in years
    "sex",       # 1 = male, 0 = female
    "cp",        # chest pain type, 1-4
    "trestbps",  # resting blood pressure, mm Hg on admission
    "chol",      # serum cholesterol, mg/dl
    "fbs",       # fasting blood sugar > 120 mg/dl (1 = true)
    "restecg",   # resting electrocardiographic result, 0-2
    "thalach",   # maximum heart rate achieved
    "exang",     # exercise-induced angina (1 = yes)
    "oldpeak",   # ST depression induced by exercise relative to rest
    "slope",     # slope of the peak exercise ST segment, 1-3
    "ca",        # number of major vessels (0-3) coloured by fluoroscopy
    "thal",      # thalassemia / defect type: 3, 6, 7
    "num",       # diagnosis: 0 = no significant disease, 1-4 = increasing severity
]

# Human-readable description used by `analysis.data_dictionary()` and the report.
COLUMN_DESCRIPTIONS = {
    "age": "Age in years",
    "sex": "Biological sex (1 = male, 0 = female)",
    "cp": "Chest pain type (1-4)",
    "trestbps": "Resting blood pressure (mm Hg)",
    "chol": "Serum cholesterol (mg/dl)",
    "fbs": "Fasting blood sugar > 120 mg/dl (1 = true)",
    "restecg": "Resting ECG result (0-2)",
    "thalach": "Maximum heart rate achieved (bpm)",
    "exang": "Exercise-induced angina (1 = yes)",
    "oldpeak": "ST depression induced by exercise vs. rest",
    "slope": "Slope of the peak exercise ST segment (1-3)",
    "ca": "Major vessels coloured by fluoroscopy (0-3)",
    "thal": "Defect type (3 = normal, 6 = fixed, 7 = reversible)",
    "num": "Diagnosis: 0 = no significant disease, 1-4 = severity",
}

# The archive encodes every missing value as a literal "?".
NA_VALUES = ["?"]

# --------------------------------------------------------------------------
# Code -> label maps
# --------------------------------------------------------------------------
# Analysing raw integer codes is how you end up reporting "mean sex = 0.68".
# `analysis.decode_categoricals` turns each of these into a labelled column.

SEX_LABELS = {0: "female", 1: "male"}

CP_LABELS = {
    1: "typical angina",
    2: "atypical angina",
    3: "non-anginal pain",
    4: "asymptomatic",
}

RESTECG_LABELS = {
    0: "normal",
    1: "ST-T abnormality",
    2: "left ventricular hypertrophy",
}

SLOPE_LABELS = {1: "upsloping", 2: "flat", 3: "downsloping"}

THAL_LABELS = {3: "normal", 6: "fixed defect", 7: "reversible defect"}

YES_NO_LABELS = {0: "no", 1: "yes"}

# Applied by `decode_categoricals`: source column -> (new column, mapping).
LABEL_MAPS = {
    "sex": ("sex_label", SEX_LABELS),
    "cp": ("cp_label", CP_LABELS),
    "restecg": ("restecg_label", RESTECG_LABELS),
    "slope": ("slope_label", SLOPE_LABELS),
    "thal": ("thal_label", THAL_LABELS),
    "fbs": ("fbs_label", YES_NO_LABELS),
    "exang": ("exang_label", YES_NO_LABELS),
}

# --------------------------------------------------------------------------
# Data-quality rules
# --------------------------------------------------------------------------
# Sentinel zeros. A living patient cannot have a serum cholesterol or a resting
# blood pressure of 0 — these are "not measured" recorded as 0. The Switzerland
# database in particular stores almost all of its cholesterol values this way,
# so treating 0 as a real number drags every cross-site mean downwards.
ZERO_AS_MISSING = ["chol", "trestbps"]

# Values outside these ranges are implausible and are treated as missing.
# Bounds are deliberately wide — the aim is to catch coding errors, not to
# quietly delete genuine outliers.
PLAUSIBLE_RANGES = {
    "age": (18, 110),
    "trestbps": (60, 260),
    "chol": (80, 700),
    "thalach": (50, 240),
    "oldpeak": (-3.0, 8.0),
}

# Rows missing any of these cannot be used for the questions we ask, so they are
# dropped rather than imputed.
REQUIRED_COLUMNS = ["age", "sex", "num"]

# --------------------------------------------------------------------------
# Derived features
# --------------------------------------------------------------------------

# Age bands. Right-open bins, so 40 falls in "40-49", matching how clinical
# age groups are normally written.
AGE_BIN_EDGES = [0, 40, 50, 60, 70, 200]
AGE_BIN_LABELS = ["<40", "40-49", "50-59", "60-69", "70+"]

# Cholesterol categories, following the common NCEP ATP III thresholds.
CHOL_BIN_EDGES = [0, 200, 240, 10_000]
CHOL_BIN_LABELS = ["desirable (<200)", "borderline (200-239)", "high (240+)"]

# Blood-pressure categories for resting systolic pressure (mm Hg).
BP_BIN_EDGES = [0, 120, 130, 140, 1_000]
BP_BIN_LABELS = ["normal (<120)", "elevated (120-129)", "stage 1 (130-139)", "stage 2 (140+)"]

# --------------------------------------------------------------------------
# Output files
# --------------------------------------------------------------------------

CLEAN_CSV = "heart_clean.csv"          # missing values preserved as empty cells
IMPUTED_CSV = "heart_imputed.csv"      # group-median / group-mode imputed
SUMMARY_REPORT = "summary_stats.md"
