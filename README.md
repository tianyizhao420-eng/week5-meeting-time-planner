# meeting-time-planner

A reusable AI skill that converts a proposed meeting time across multiple cities,
flags whether each slot falls within working hours, and detects public holidays —
all in one command.

**Video demo:** _[add your Zoom / YouTube link here]_

---

## What the skill does

Given a meeting time (e.g., "Tuesday 3 PM New York") and a list of target cities,
the skill produces a table showing:

| City | Local Time | Day | Working Hours? | Holiday? |
|------|-----------|-----|---------------|----------|
| London | 20:00 Tue | Tuesday | No (After 18:00) | No |
| Tokyo | 04:00 Wed | Wednesday | No (Before 09:00) | No |
| Sydney | 05:00 Wed | Wednesday | No (Before 09:00) | No |
| Berlin | 21:00 Tue | Tuesday | No (After 18:00) | No |

It then recommends better alternatives or flags holidays that should prompt
the organiser to reschedule.

---

## Why I chose this topic

Timezone arithmetic looks trivial but breaks constantly in practice:
daylight-saving transitions shift offsets mid-year, countries have different
DST rules, and "is 4 PM New York a good time for Sydney?" requires exact math
that a language model cannot do reliably from training knowledge alone.
Holiday lookup is even harder: the model's training data may be stale, country
or regional holidays vary, and the model cannot query a live calendar.

A Python script is **genuinely load-bearing** here — it is not decorative.
Without the script, the skill would produce plausible-sounding but incorrect
results (e.g., wrong UTC offset after a DST change, missed regional holidays).

---

## How to use

### Prerequisites

```bash
pip install pytz holidays
```

### Folder structure

```
hw5-meeting-time-planner/
├── .agents/
│   └── skills/
│       └── meeting-time-planner/
│           ├── SKILL.md
│           ├── scripts/
│           │   └── convert_meeting_time.py
│           └── references/
│               └── supported-cities.md
└── README.md
```

### Invoking the script directly

```bash
python3 .agents/skills/meeting-time-planner/scripts/convert_meeting_time.py \
  --time "2025-06-10 15:00" \
  --source "New York" \
  --cities "London,Tokyo,Sydney,Berlin"
```

### Invoking via a coding assistant (Claude Code, Copilot Agent, Codex)

The agent reads `SKILL.md` and recognises the skill from its description
when you ask something like:

> "Check if 3 PM New York on June 10 works for London, Tokyo, Sydney, and Berlin."

The agent will run the script, parse the JSON output, and present it as
a Markdown table with a brief recommendation.

---

## What the script does

`scripts/convert_meeting_time.py` handles every deterministic step:

1. **Parses** the meeting datetime from multiple common formats
   (`YYYY-MM-DD HH:MM`, `MM/DD/YYYY HH:MM`, ISO 8601, etc.)
2. **Resolves** city names to IANA timezone strings via a built-in lookup
   table of 90+ cities; also accepts raw IANA strings (`America/New_York`)
   and performs fuzzy partial matching for common abbreviations
3. **Converts** the source time to each target city using `pytz`, which
   correctly applies DST transitions for the exact date provided
4. **Checks working hours**: Monday–Friday 09:00–18:00 local time; returns
   a human-readable reason when outside (e.g., "Weekend (Saturday)",
   "Before 09:00 (04:00)")
5. **Detects public holidays** using the `holidays` package, which covers
   ~100 countries and includes national, regional, and state-level holidays;
   returns the holiday name (e.g., "Independence Day", "Noël")
6. **Outputs structured JSON** that the agent formats into a Markdown table

---

## Sample outputs

### Normal case — 3 PM New York → 4 cities

```bash
python3 ... --time "2025-06-10 15:00" --source "New York" \
            --cities "London,Tokyo,Sydney,Berlin"
```

| City | Local Time | Day | Working Hours? | Holiday? |
|------|-----------|-----|---------------|----------|
| London | 20:00 Tue | Tuesday | No (After 18:00) | No |
| Tokyo | 04:00 Wed | Wednesday | No (Before 09:00) | No |
| Sydney | 05:00 Wed | Wednesday | No (Before 09:00) | No |
| Berlin | 21:00 Tue | Tuesday | No (After 18:00) | No |

**Recommendation:** No overlap within working hours exists. For London + Berlin,
try 09:00–11:00 New York time. Tokyo and Sydney cannot join during business hours
on the same day.

### Holiday detection — Christmas Day

```bash
python3 ... --time "2025-12-25 10:00" --source "America/New_York" \
            --cities "London,Paris,Tokyo,Sydney"
```

London (15:00) and Paris (16:00) fall within working hours — but both are
**Christmas Day** (public holiday). Sydney lands on Boxing Day. The organiser
should reschedule.

### Edge case — weekend + cross-date-line shift

```bash
python3 ... --time "2025-06-14 10:00" --source "Singapore" \
            --cities "London,New York,Tokyo"
```

Singapore Saturday 10:00 → London Saturday 03:00 (weekend + before-hours),
New York Friday 22:00 (after-hours), Tokyo Saturday 11:00 (weekend). No slot works.

### Cautious case — unknown city

```bash
python3 ... --source "Xyz123" --cities "London" --time "..."
```

The script exits with a clear error listing all supported city names and
suggests passing an IANA timezone string instead. The agent relays this
to the user rather than guessing.

---

## What worked well

- `pytz` handles DST transitions and historical offset changes accurately for any
  date, which prose cannot replicate
- The `holidays` package returns localised holiday names (e.g., "Noël" in France)
  and covers both national and regional holidays out of the box
- Fuzzy city matching lets users write "LA", "NYC", "SF" without memorising exact names
- Structured JSON output keeps the model's job simple: it only needs to format,
  not compute

## Limitations

- Working hours are fixed at Mon–Fri 09:00–18:00. Custom hours (e.g., a company
  that works 08:00–17:00, or a Middle-Eastern firm with a Sun–Thu week) are not
  supported without editing the script
- One datetime at a time; finding the best slot across a range of options requires
  calling the script repeatedly
- Regional holidays below the subdivision level (e.g., city-specific closures,
  school holidays) are not included
- The city lookup table covers ~90 cities; cities not listed require an IANA string
