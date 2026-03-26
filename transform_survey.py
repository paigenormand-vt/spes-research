"""
transform_survey.py
-------------------
Converts a QuestionPro survey export (updated-data.csv) into the clean
data.csv that the SPES undergraduate research website reads.

Usage:
    python3 transform_survey.py

Input:  updated-data.csv  (raw QuestionPro export — place in same folder)
Output: data.csv          (17-column clean file for the website)

The script is resilient to the metadata rows QuestionPro prepends to every
export (e.g. "Data Export Generated on...", "Survey ID..."). It finds the
real header row automatically and only processes rows with status "Completed",
so partially-filled or terminated responses are automatically skipped.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAINTENANCE: When new faculty respond to the survey, add them to the two
dictionaries below before running the script.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import csv
import re
import os

# ── Manual overrides ──────────────────────────────────────────────────────────
# Faculty names are not collected by the survey.
# Keys are 1-based sequential position among COMPLETED responses (i.e. the
# 1st completed response = 1, 2nd = 2, etc.).
# Add a new entry here for each new respondent before running the script.
# If a key is missing, the card will show a blank faculty name on the website.

FACULTY_NAMES = {
    1:  "Dr. David Schmale",
    2:  "Dr. Michael Flessner",
    3:  "Dr. Vijay Chaganti",
    4:  "Dr. Priyamvada Voothuluru",
    5:  "Niki (Schmale Lab)",
    6:  "Dr. Guillaume Pilot",
    7:  "Dr. Eric Stallknecht",
    8:  "Dr. Ryan Stewart",
    9:  "Dr. Carol Leisner",
    10: "Plant Disease Clinic (PDC)",
    11: "Dr. Shilai Hao",
    12: "Dr. Ashley Jernigan",
    13: "Dr. Bingyu Zhao",
    14: "Dr. Harner",
    15: "Dr. Meredith Steele",
    16: "Dr. John Jelesko",
    17: "Dr. Benjamin Tracy",
    18: "Dr. J. L. Reid",
    19: "Dr. D. Sandor",
    20: "Dr. Xu Zhang",
    21: "Dr. Huijie Gan",
}

# Use when the survey's topic/title field was left blank for a row.
# Keys match the same 1-based sequential position as FACULTY_NAMES above.
TITLE_OVERRIDES = {
    4:  "Plant Physiology — Drought Stress Research",
    20: "Plant Physiology and Environmental Responses",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_email(raw):
    """Pull address out of '[Email] xxx@vt.edu' or return raw if already clean."""
    m = re.search(r'[\w.+-]+@[\w.-]+\.\w+', raw)
    return m.group(0) if m else raw.strip()


def extract_website(raw):
    """Return the first usable URL found in the field."""
    m = re.search(r'https?://[^\s,;)]+', raw)
    if m:
        return m.group(0).rstrip('.,;)/')
    m = re.search(r'www\.[^\s,;)]+', raw)
    if m:
        return 'https://' + m.group(0).rstrip('.,;)/')
    return ''


def clean_text(val):
    """Normalise whitespace."""
    return ' '.join(val.split()).strip()


def clean_description(val):
    """
    Remove any leading URL that some faculty paste into the description field,
    and normalise whitespace.
    """
    val = val.strip()
    val = re.sub(r'^https?://\S+\s*', '', val)
    val = re.sub(r'^www\.\S+\s*', '', val)
    return clean_text(val)


def normalize_none(val):
    """Return empty string for 'none', 'no', 'n/a', 'not applicable', etc."""
    if val.strip().lower() in ('none', 'no', 'n/a', 'na', 'no.', 'none.',
                               'not applicable', 'not applicable '):
        return ''
    return val.strip()


def build_pipe(flags, labels):
    """Build a pipe-separated string from parallel flag/label lists."""
    return '|'.join(label for flag, label in zip(flags, labels) if str(flag).strip() == '1')


def derive_stripe_class(envs):
    """Derive the card stripe class from the environments string."""
    parts = set(envs.split('|')) if envs else set()
    if 'field' in parts and len(parts) > 1:
        return 'mixed'
    if 'field' in parts:
        return 'field'
    if 'computational' in parts and 'lab' not in parts:
        return 'computational'
    return 'lab'


# ── Header detection ──────────────────────────────────────────────────────────

def find_header_row(all_rows):
    """
    Return the index of the main header row (the one containing 'Response ID').
    QuestionPro prepends metadata rows before the headers; this detection makes
    the script resilient to that changing in future exports.
    """
    for i, row in enumerate(all_rows):
        if row and row[0].strip() == 'Response ID':
            return i
    raise ValueError(
        "Could not find a header row containing 'Response ID'. "
        "Check that the input file is an unmodified QuestionPro export."
    )


# ── Column index map ──────────────────────────────────────────────────────────
# Based on the QuestionPro export format for this survey.
# If the survey is ever redesigned and columns shift, re-inspect with:
#   python3 -c "
#   import csv
#   rows = list(csv.reader(open('updated-data.csv', encoding='utf-8-sig')))
#   hi = next(i for i,r in enumerate(rows) if r and r[0]=='Response ID')
#   [print(i, rows[hi][i]!r, '/', rows[hi+1][i]!r) for i in range(len(rows[hi])) if rows[hi][i] or rows[hi+1][i]]
#   "

COL = {
    'status':               1,
    'topic':                18,
    'env_field':            19,
    'env_lab':              20,
    'env_comp':             21,
    'env_other':            22,   # sometimes contains activities text
    'activities':           23,
    'pos_volunteer':        24,
    'pos_wage':             25,
    'pos_credit':           26,
    'tl_fall':              27,
    'tl_spring':            28,
    'tl_summer':            29,
    'tl_anytime':           30,
    'tl_other':             31,
    'prior_knowledge':      32,
    'standing_fr':          33,
    'standing_so':          34,
    'standing_jr':          35,
    'standing_sr':          36,
    'time_commitment':      37,
    'email':                38,
    'special_requirements': 41,
    'description':          42,
    'website':              43,
}

MIN_COLUMNS = max(COL.values()) + 1


# ── Main transform ─────────────────────────────────────────────────────────────

def transform(input_filename='updated-data.csv', output_filename='data.csv'):
    script_dir  = os.path.dirname(os.path.abspath(__file__))
    input_path  = os.path.join(script_dir, input_filename)
    output_path = os.path.join(script_dir, output_filename)

    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Input file not found: {input_path}\n"
            f"Make sure '{input_filename}' is in the same folder as this script."
        )

    with open(input_path, newline='', encoding='utf-8-sig') as f:
        all_rows = list(csv.reader(f))

    header_idx = find_header_row(all_rows)
    # Skip main header row AND the sub-header row (checkbox labels like "Field", "Lab"…)
    data_rows = all_rows[header_idx + 2:]

    # Filter to completed responses only — skips Terminated/Started rows automatically
    completed = [
        row for row in data_rows
        if len(row) > COL['status'] and row[COL['status']].strip() == 'Completed'
    ]

    if not completed:
        print("Warning: no completed responses found. Check the input file.")
        return

    out_rows = []
    for seq, col in enumerate(completed, start=1):
        # Pad short rows so index access is always safe
        while len(col) < MIN_COLUMNS:
            col.append('')

        def c(key):
            return col[COL[key]]

        # ── ID (sequential position among completed responses) ─────────────
        row_id = seq

        # ── Title ──────────────────────────────────────────────────────────
        title = clean_text(c('topic')) or TITLE_OVERRIDES.get(row_id, '')
        if not title:
            print(f"  Warning: row {row_id} ({FACULTY_NAMES.get(row_id, 'unknown')}) "
                  f"has no title — add one to TITLE_OVERRIDES.")

        # ── Faculty ────────────────────────────────────────────────────────
        faculty = FACULTY_NAMES.get(row_id, '')
        if not faculty:
            print(f"  Warning: no faculty name for row {row_id} — add one to FACULTY_NAMES.")

        # ── Contact ────────────────────────────────────────────────────────
        email   = extract_email(c('email')) if c('email').strip() else ''
        website = extract_website(c('website')) if c('website').strip() else ''

        # ── Topic (mirrors title) ──────────────────────────────────────────
        topic = title

        # ── Environments ───────────────────────────────────────────────────
        environments = build_pipe(
            [c('env_field'), c('env_lab'), c('env_comp')],
            ['field',        'lab',        'computational']
        )

        # ── Activities ─────────────────────────────────────────────────────
        # Some faculty put activities in the "Other" environment text box instead.
        activities = clean_text(c('activities'))
        if not activities and c('env_other').strip():
            activities = clean_text(re.sub(r'^\[Other\]\s*', '', c('env_other')))

        # ── Description ────────────────────────────────────────────────────
        description = clean_description(c('description'))

        # ── Positions ──────────────────────────────────────────────────────
        positions = build_pipe(
            [c('pos_volunteer'), c('pos_wage'), c('pos_credit')],
            ['volunteer',        'wage',        'credit']
        )

        # ── Timeline ───────────────────────────────────────────────────────
        timeline = build_pipe(
            [c('tl_fall'), c('tl_spring'), c('tl_summer'), c('tl_anytime')],
            ['fall',       'spring',       'summer',       'anytime']
        )
        other_tl = clean_text(re.sub(r'^\[Other\]\s*', '', c('tl_other')))
        if other_tl and other_tl.lower() not in (timeline.split('|') if timeline else []):
            timeline = (timeline + '|' + other_tl) if timeline else other_tl

        # ── Standing ───────────────────────────────────────────────────────
        standing = build_pipe(
            [c('standing_fr'), c('standing_so'), c('standing_jr'), c('standing_sr')],
            ['freshman',       'sophomore',      'junior',         'senior']
        )

        # ── Other fields ───────────────────────────────────────────────────
        time_commitment      = clean_text(c('time_commitment'))
        prior_knowledge      = normalize_none(c('prior_knowledge'))
        special_requirements = normalize_none(c('special_requirements'))
        lab_note             = ''   # populated manually in data.csv when needed

        out_rows.append([
            row_id,
            title,
            faculty,
            email,
            website,
            topic,
            environments,
            activities,
            description,
            positions,
            timeline,
            standing,
            time_commitment,
            prior_knowledge,
            special_requirements,
            lab_note,
            derive_stripe_class(environments),
        ])

    headers = [
        'id', 'title', 'faculty', 'email', 'website', 'topic',
        'environments', 'activities', 'description', 'positions',
        'timeline', 'standing', 'time_commitment', 'prior_knowledge',
        'special_requirements', 'lab_note', 'stripe_class',
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(headers)
        writer.writerows(out_rows)

    print(f"Done — wrote {len(out_rows)} rows to {output_path}")
    missing_names = [i for i in range(1, len(out_rows) + 1) if not FACULTY_NAMES.get(i)]
    if missing_names:
        print(f"  Action needed: add faculty names for row(s): {missing_names}")


if __name__ == '__main__':
    transform()
