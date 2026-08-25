# VitalsFrame — Summary Statistics Report

*Generated 2026-08-07 from the UCI Heart Disease databases.*

## Dataset at a glance

- **Patients:** 920
- **Columns:** 31 (14 source attributes + derived and metadata)
- **Contributing institutions:** 4
- **Overall disease prevalence:** 55.3%
- **Missing measured values:** 1,932 of 12,880 (15.0%)

## Missing data

Percentage missing per column, by source database. The gaps are not random — they cluster almost entirely by institution, which is why any pooled analysis of `ca`, `thal` or `slope` is effectively an analysis of Cleveland.

| site        |   age |   sex |   cp |   trestbps |   chol |   fbs |   restecg |   thalach |   exang |   oldpeak |   slope |   ca |   thal |   num |
|:------------|------:|------:|-----:|-----------:|-------:|------:|----------:|----------:|--------:|----------:|--------:|-----:|-------:|------:|
| cleveland   |     0 |     0 |    0 |        0   |    0   |   0   |       0   |       0   |     0   |       0   |     0   |  1.3 |    0.7 |     0 |
| hungary     |     0 |     0 |    0 |        0.3 |    7.8 |   2.7 |       0.3 |       0.3 |     0.3 |       0   |    64.6 | 99   |   90.5 |     0 |
| long_beach  |     0 |     0 |    0 |       28.5 |   28   |   3.5 |       0   |      26.5 |    26.5 |      28   |    51   | 99   |   83   |     0 |
| switzerland |     0 |     0 |    0 |        1.6 |  100   |  61   |       0.8 |       0.8 |     0.8 |       4.9 |    13.8 | 95.9 |   42.3 |     0 |

## Numeric distributions

|          |   count |   mean |   std |   min |   25% |   50% |   75% |   max |
|:---------|--------:|-------:|------:|------:|------:|------:|------:|------:|
| age      |     920 |   53.5 |   9.4 |  28   |    47 |  54   |  60   |  77   |
| trestbps |     860 |  132.3 |  18.5 |  80   |   120 | 130   | 140   | 200   |
| chol     |     718 |  246.8 |  58.5 |  85   |   210 | 239.5 | 276.8 | 603   |
| thalach  |     865 |  137.5 |  25.9 |  60   |   120 | 140   | 157   | 202   |
| oldpeak  |     858 |    0.9 |   1.1 |  -2.6 |     0 |   0.5 |   1.5 |   6.2 |

## Questions explored

### Q1. Mean cholesterol by age group

| age_group   |   n_measured |   mean |   median |   std |   n_patients |
|:------------|-------------:|-------:|---------:|------:|-------------:|
| <40         |           66 |  232.9 |      220 |  64   |           80 |
| 40-49       |          181 |  243.2 |      238 |  53.2 |          212 |
| 50-59       |          293 |  249.1 |      236 |  61.8 |          375 |
| 60-69       |          155 |  254   |      252 |  56.2 |          222 |
| 70+         |           23 |  238.5 |      225 |  49.1 |           31 |

### Q1b. Mean cholesterol by age group and sex

| age_group   |   female |   male |
|:------------|---------:|-------:|
| <40         |    206.8 |  241.9 |
| 40-49       |    234.3 |  246.3 |
| 50-59       |    273   |  241.7 |
| 60-69       |    279.2 |  245.8 |
| 70+         |    236.4 |  239.1 |

### Q2. Disease rate by age group and sex

| age_group   | sex_label   |   n_patients |   n_with_disease |   disease_rate_pct |
|:------------|:------------|-------------:|-----------------:|-------------------:|
| <40         | female      |           19 |                3 |               15.8 |
| <40         | male        |           61 |               23 |               37.7 |
| 40-49       | female      |           53 |                6 |               11.3 |
| 40-49       | male        |          159 |               79 |               49.7 |
| 50-59       | female      |           72 |               20 |               27.8 |
| 50-59       | male        |          303 |              193 |               63.7 |
| 60-69       | female      |           44 |               20 |               45.5 |
| 60-69       | male        |          178 |              143 |               80.3 |
| 70+         | female      |            6 |                1 |               16.7 |
| 70+         | male        |           25 |               21 |               84   |

### Q3. Vitals by disease status

| vital    | statistic   |   disease |   no disease |
|:---------|:------------|----------:|-------------:|
| age      | mean        |      55.9 |         50.5 |
| age      | median      |      57   |         51   |
| age      | count       |     509   |        411   |
| trestbps | mean        |     134.3 |        129.9 |
| trestbps | median      |     130   |        130   |
| trestbps | count       |     469   |        391   |
| chol     | mean        |     254   |        240.2 |
| chol     | median      |     248   |        233   |
| chol     | count       |     346   |        372   |
| thalach  | mean        |     128.3 |        148.8 |
| thalach  | median      |     128   |        151   |
| thalach  | count       |     474   |        391   |
| oldpeak  | mean        |       1.3 |          0.4 |
| oldpeak  | median      |       1   |          0   |
| oldpeak  | count       |     468   |        390   |

### Q4. Disease rate by chest pain type

| cp_label         |   n_patients |   n_with_disease |   disease_rate_pct |
|:-----------------|-------------:|-----------------:|-------------------:|
| asymptomatic     |          496 |              392 |               79   |
| typical angina   |           46 |               20 |               43.5 |
| non-anginal pain |          204 |               73 |               35.8 |
| atypical angina  |          174 |               24 |               13.8 |

### Q5. Max heart rate by age group and diagnosis

| age_group   |   disease |   no disease |
|:------------|----------:|-------------:|
| <40         |     145.5 |        163   |
| 40-49       |     134.9 |        153.4 |
| 50-59       |     127   |        144.8 |
| 60-69       |     124.3 |        138.2 |
| 70+         |     119.1 |        127.9 |

### Q6. Profile of the four contributing institutions

| institution                         |   n_patients |   mean_age |   pct_male |   mean_chol |   chol_measured |   disease_rate_pct |   chol_coverage_pct |
|:------------------------------------|-------------:|-----------:|-----------:|------------:|----------------:|-------------------:|--------------------:|
| Cleveland Clinic Foundation         |          303 |       54.4 |       68   |       246.7 |             303 |               45.9 |               100   |
| Hungarian Institute of Cardiology   |          294 |       47.8 |       72.4 |       250.8 |             271 |               36.1 |                92.2 |
| University Hospitals Zurich & Basel |          123 |       55.3 |       91.9 |       nan   |               0 |               93.5 |                 0   |
| V.A. Medical Center                 |          200 |       59.4 |       97   |       239.6 |             144 |               74.5 |                72   |

### Q7. Diagnosis severity by institution

| institution                         |   0 |   1 |   2 |   3 |   4 |   All |
|:------------------------------------|----:|----:|----:|----:|----:|------:|
| Cleveland Clinic Foundation         | 164 |  55 |  36 |  35 |  13 |   303 |
| Hungarian Institute of Cardiology   | 188 | 106 |   0 |   0 |   0 |   294 |
| University Hospitals Zurich & Basel |   8 |  48 |  32 |  30 |   5 |   123 |
| V.A. Medical Center                 |  51 |  56 |  41 |  42 |  10 |   200 |
| All                                 | 411 | 265 | 109 | 107 |  28 |   920 |

## Data dictionary

| column   | description                                           |
|:---------|:------------------------------------------------------|
| age      | Age in years                                          |
| sex      | Biological sex (1 = male, 0 = female)                 |
| cp       | Chest pain type (1-4)                                 |
| trestbps | Resting blood pressure (mm Hg)                        |
| chol     | Serum cholesterol (mg/dl)                             |
| fbs      | Fasting blood sugar > 120 mg/dl (1 = true)            |
| restecg  | Resting ECG result (0-2)                              |
| thalach  | Maximum heart rate achieved (bpm)                     |
| exang    | Exercise-induced angina (1 = yes)                     |
| oldpeak  | ST depression induced by exercise vs. rest            |
| slope    | Slope of the peak exercise ST segment (1-3)           |
| ca       | Major vessels coloured by fluoroscopy (0-3)           |
| thal     | Defect type (3 = normal, 6 = fixed, 7 = reversible)   |
| num      | Diagnosis: 0 = no significant disease, 1-4 = severity |
