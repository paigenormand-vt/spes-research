# SPES Undergraduate Research Opportunities

A searchable, filterable directory of undergraduate research opportunities offered by faculty in the **School of Plant and Environmental Sciences (SPES) at Virginia Tech**.

🔗 **Live site:** [paigenormand-vt.github.io/spes-research](https://paigenormand-vt.github.io/spes-research/)

---

## What This Is

A self-contained, static web page that lets students browse faculty research labs, filter by environment (field/lab/computational), position type, student standing, and availability, and contact faculty directly. No server, no database, no framework — just two files.

---

## Files

| File | Purpose |
|---|---|
| `spes-undergrad-research.html` | The entire website (HTML, CSS, and JavaScript in one file) |
| `data.csv` | The structured data powering all the cards — **edit this to update content** |
| `updateddata.csv` | Raw QuestionPro survey export — archive only, not loaded by the site |
| `transform_survey.py` | Python script that converts `updated-data.csv` → `data.csv` |

---

## Updating Content

### Quickest update — editing `data.csv` directly on GitHub

1. Click on `data.csv` in this repository
2. Click the **pencil icon (✏️)** to edit
3. Make your changes
4. Scroll down and click **Commit changes**

The live site updates within ~60 seconds. Do a hard refresh (`Ctrl+Shift+R` / `Cmd+Shift+R`) to see changes immediately.

### Adding multiple new entries from a survey export

1. Export the latest responses from QuestionPro as CSV and save it as `updated-data.csv`
2. Update the `FACULTY_NAMES` dictionary in `transform_survey.py` with any new respondent IDs
3. Run the script:
   ```bash
   python3 transform_survey.py
   ```
4. Review the output `data.csv`, then upload it to this repository

> ⚠️ Faculty names are not collected by the survey and must be added manually to `FACULTY_NAMES` in the script before running it.

---

## Data Format

`data.csv` has 17 columns. Multi-value fields use `|` as a separator (e.g., `field|lab`).

| Column | Allowed Values |
|---|---|
| `environments` | `field` · `lab` · `computational` |
| `positions` | `wage` · `credit` · `volunteer` |
| `timeline` | `fall` · `spring` · `summer` · `anytime` |
| `standing` | `freshman` · `sophomore` · `junior` · `senior` |
| `stripe_class` | `field` · `lab` · `computational` · `mixed` |

Values are case-sensitive and must be lowercase.

---

## Running Locally

The site uses `fetch()` to load the CSV, so it can't be opened directly as a local file. Use a simple local server instead:

```bash
python -m http.server 8000
# Then open: http://localhost:8000/spes-undergrad-research.html
```

Or use the **Live Server** extension in VS Code.

---

## Maintainer

Paige Normand · Academic Advisor, SPES · [paigenormand@vt.edu](mailto:paigenormand@vt.edu)
