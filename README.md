# VitalsFrame — Health Dataset Explorer 

A Pandas exploration of four real clinical databases of patients referred for coronary
angiography. The pipeline loads, inspects, cleans and cross-tabulates 920 patient records
from four hospitals, and answers a set of domain questions about cholesterol, blood
pressure, heart rate and disease prevalence.

The interesting part of this dataset is not the modelling — it is that **the four
databases share a schema but not a data-collection culture**. Most of the work here is
about noticing that, and making sure the summary statistics do not quietly lie about it.

📓 **[Read the analysis notebook →](notebooks/exploration.ipynb)**
📊 **[Generated statistics report →](reports/summary_stats.md)**

---

## Dataset

**UCI Machine Learning Repository — Heart Disease (1988).**
[archive.ics.uci.edu/dataset/45/heart+disease](https://archive.ics.uci.edu/dataset/45/heart+disease)

920 patients across four institutions, 14 attributes each plus a diagnosis graded 0–4: 

| Database | Institution | Patients |
|---|---|---:|
| `cleveland` | Cleveland Clinic Foundation | 303 |
| `hungary` | Hungarian Institute of Cardiology, Budapest | 294 |
| `long_beach` | V.A. Medical Center, Long Beach, CA | 200 |
| `switzerland` | University Hospitals Zurich & Basel | 123 |

**License.** Released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
The archive carries a publication request that the principal investigators be credited:

> Andras Janosi, M.D. (Budapest); William Steinbrunn, M.D. (Zurich);
> Matthias Pfisterer, M.D. (Basel); Robert Detrano, M.D., Ph.D. (Cleveland & Long Beach).
> Donated by David W. Aha.

**Citation.** Detrano, R., Janosi, A., Steinbrunn, W., Pfisterer, M., Schmid, J.,
Sandhu, S., Guppy, K., Lee, S., & Froelicher, V. (1989). *International application of a
new probability algorithm for the diagnosis of coronary artery disease.*
American Journal of Cardiology, 64, 304–310.

> ⚠️ This is a 1988 referral cohort, not a population sample. Every patient here was
> already suspected of coronary disease. The rates below describe *this cohort* and
> should not be read as general-population prevalence.

---

## Questions explored

1. **How does serum cholesterol vary by age group?** (and by age × sex)
2. **How does disease prevalence vary by age group and sex?**
3. **Which vitals actually separate diagnosed from healthy patients?**
4. **Which presenting chest-pain type carries the highest disease rate?**
5. **How does maximum achieved heart rate vary with age and diagnosis?**
6. **How do the four contributing institutions compare?**
7. **How is diagnosis severity distributed across sites?**

---

## Key findings

**1. The missing data is structural, not random.**
`ca` (fluoroscopy) and `thal` (thallium scan) are missing for 90–99% of patients outside
Cleveland — those hospitals simply did not run those tests. A pooled analysis of those
columns is really an analysis of Cleveland wearing a sample size of 920.

| site | trestbps | chol | slope | ca | thal |
|---|---:|---:|---:|---:|---:|
| cleveland | 0.0 | 0.0 | 0.0 | 1.3 | 0.7 |
| hungary | 0.3 | 7.8 | 64.6 | 99.0 | 90.5 |
| long_beach | 28.5 | 28.0 | 51.0 | 99.0 | 83.0 |
| switzerland | 1.6 | **100.0** | 13.8 | 95.9 | 42.3 |

**2. 172 cholesterol values are sentinel zeros.**
All 123 Swiss readings, plus 49 at Long Beach, are recorded as `0` — a serum cholesterol
that is not compatible with life. They are unrecorded measurements, not low ones, and
nothing in the file flags them. Averaging them in moves the pooled mean from
**247 mg/dl to 199 mg/dl**, relabelling the whole cohort from "high" to "desirable".

**3. Maximum heart rate separates the groups far better than cholesterol.** 
`thalach` is 128 bpm in diagnosed patients against 149 bpm in the rest — a 20 bpm gap.
Cholesterol differs by only 14 mg/dl, well inside its 58 mg/dl standard deviation.
A heart that cannot raise its rate under exercise is the signal.

**4. Cholesterol crosses over by sex at around age 50.**
Women sit ~35 mg/dl *below* men in their thirties and ~33 mg/dl *above* them by their
sixties — the post-menopausal lipid shift, visible in 920 patients from 1988.

**5. Asymptomatic patients have the highest disease rate (79%)**, above textbook typical
angina (43.5%). A referral-selection effect: someone with no chest pain who is sent for
angiography anyway got there because something else was alarming.

**6. Hungary only ever coded severity 0 or 1** where the other three sites used the full
0–4 scale — so the binary `has_disease` (`num > 0`) is the only target comparable across
all four databases.

---

## Setup 

```bash
git clone <this-repo>
cd vitalsframe

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

The raw data is committed to `data/raw/`. To re-download it from UCI:

```bash
python -m src.fetch_data
```

### Run the pipeline 

```bash
python -m src.analysis              # clean, export both CSVs, write the report
python -m src.analysis --show       # ...and print every answer table to stdout
```

Output:

```
Loading four source databases ...
  loaded 920 raw patient records
Cleaning ...
  920 records retained (0 dropped for missing key fields)
  1,932 / 12,880 measured values missing (15.0%)
Wrote data/clean/heart_clean.csv
Wrote data/clean/heart_imputed.csv
Wrote reports/summary_stats.md
```

### Open the notebook

```bash
jupyter lab notebooks/exploration.ipynb
```

---

## How the cleaning works

`analysis.clean()` chains the steps with `DataFrame.pipe`, so the order reads top to bottom:

| step | what it does |
|---|---|
| `coerce_dtypes` | float measurements; nullable `Int64` for code columns |
| `flag_sentinel_zeros` | impossible `0`s in `chol` / `trestbps` → `NaN` |
| `enforce_ranges` | values outside physiological bounds → `NaN` |
| `drop_incomplete` | drop rows missing age / sex / diagnosis |
| `decode_categoricals` | `1` → `"male"`, `4` → `"asymptomatic"`, … |
| `add_derived` | `age_group`, `chol_group`, `bp_group`, `has_disease` |
| `attach_site_metadata` | left-join the institution lookup table |

### Two exports, on purpose

- **`data/clean/heart_clean.csv`** — gaps stay gaps. Honest, and correct for reporting.
- **`data/clean/heart_imputed.csv`** — gaps filled *within site* (median for
  measurements, mode for codes), for tools that cannot accept `NaN`. Imputing globally
  would import Cleveland's patient profile into Switzerland's rows.

Imputation does not create information. Both files ship so the choice stays explicit.

---

## Using the module directly

```python
from src import analysis

df = analysis.clean(analysis.load_all())

# Filtering: unspecified conditions are skipped
analysis.filter_patients(df, sex="female", min_age=60, has_disease=True)

# Grouped summaries
analysis.mean_cholesterol_by_age_group(df)
analysis.disease_rate_by(df, "age_group", "sex_label")

# Pivot tables
analysis.cholesterol_pivot(df)
analysis.heart_rate_by_age_and_disease(df)

# Everything at once
for title, table in analysis.answer_all(df).items():
    print(title, table, sep="\n")
```

---

## Project structure

```
vitalsframe/
├── notebooks/
│   └── exploration.ipynb      # the writeup, with outputs committed
├── src/
│   ├── config.py              # data dictionary, code→label maps, paths
│   ├── analysis.py            # load / inspect / clean / analyse / export + CLI
│   ├── report.py              # renders reports/summary_stats.md
│   └── fetch_data.py          # re-download the raw data from UCI
├── data/
│   ├── raw/                   # the four processed.* files, as published
│   └── clean/                 # generated — heart_clean.csv, heart_imputed.csv
├── reports/
│   └── summary_stats.md       # generated
├── README.md
├── requirements.txt
└── .gitignore
```

---

## Pandas techniques used

Reading headerless CSVs with a declared `na_values` · nullable `Int64` for codes with
missing values · `mask` / `where` for conditional blanking · `pipe` chains ·
`pd.cut` for binning · `map` for code→label decoding · boolean-mask filtering ·
`groupby` with named aggregation · `pivot_table` · `crosstab` · `transform` for
within-group imputation · `merge` with `validate="many_to_one"` · `concat` ·
`to_markdown` · `to_csv`.
