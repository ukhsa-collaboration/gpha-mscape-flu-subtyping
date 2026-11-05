---
title: "Flu Subtyping Report"
author: "mSCAPE Team"
format:
  mscape-html:
    code-fold: true
jupyter: python3
date: last-modified

params:
  climb_id: "TEST_ID"
  summary_json: "results/TEST_ID_flu_subtyping_summary.json"
  segment_summary_csv: "results/TEST_ID_segment_mapping_summary.csv"
  metadata_csv: "metadata.csv"
---

```{python}
#| echo: false

import json
from pathlib import Path

import pandas as pd
from IPython.display import Markdown, display

climb_id = str(params["climb_id"])
summary_json_path = Path(params["summary_json"])
segment_summary_path = Path(params["segment_summary_csv"])
metadata_path = Path(params["metadata_csv"])

for input_path in (summary_json_path, segment_summary_path, metadata_path):
    if not input_path.is_file():
        raise FileNotFoundError(f"Required report input not found: {input_path}")

summary = json.loads(summary_json_path.read_text(encoding="utf-8"))
segreadstab = pd.read_csv(segment_summary_path)
metatab = pd.read_csv(metadata_path)

# Use the ID in the summary as a consistency check against the render parameter.
if summary["climb_id"] != climb_id:
    raise ValueError(
        f"Report climb_id {climb_id!r} does not match summary "
        f"climb_id {summary['climb_id']!r}"
    )

matching_metadata = metatab.loc[metatab["climb_id"].astype(str) == climb_id]
if matching_metadata.empty:
    raise ValueError(f"No metadata row found for climb_id {climb_id!r}")

metadata_display = matching_metadata.iloc[0].to_frame(name="Value")
```

Results of mapping to the INSAFLU Reference Set for `{python} climb_id`

::: {.callout-warning}
**OFFICIAL SENSITIVE**

This product is **OFF-SEN** and should not be shared wider than its distribution without express permission from the mSCAPE team.
:::

## Sample Meta-data

```{python}
#| label: tbl-metadata
#| tbl-cap: "Sample Meta-data"

display(Markdown(metadata_display.to_markdown()))
```

## Summary Result

Subtype call from HA & NA: **`{python} summary["subtype_call"]`**

Result category:

**HA**: `{python} summary["hacall"]`  
**NA**: `{python} summary["nacall"]`

HA coverage for clade calling: `{python} summary["hacoverage"]`

Result confidence: **`{python} summary["res_conf"]`**

## Per Segment Results

```{python}
#| label: tbl-segments
#| tbl-cap: "Table of Segment Mapping Results"

segreadstab
```