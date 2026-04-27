---
name: meeting-time-planner
description: >
  Converts a proposed meeting time into the local time for each requested city,
  flags whether each slot falls within standard working hours (Mon–Fri 09:00–18:00),
  and detects public holidays in each location. Use this skill whenever the user
  asks to schedule a cross-timezone meeting, check whether a time works across
  offices, or compare what time it would be in multiple cities at once. Requires
  a Python script for accurate timezone arithmetic and holiday lookup — do NOT
  attempt to do this with prose alone.
---

# meeting-time-planner

## When to use

- User provides a date/time and wants to know what that means in several cities
- User asks "Is 3 PM New York a good time for London, Tokyo, and Sydney?"
- User asks whether a meeting slot is within business hours for each participant
- User asks whether that date is a public holiday in any of the relevant countries

## When NOT to use

- The user only wants a single timezone conversion with no business-hours check (a quick mental conversion or the system clock is enough)
- The user asks about recurring meeting series that span daylight-saving transitions across many months (this skill answers one slot at a time; repeat for each date)
- The user needs a full calendar invite or scheduling link — this skill only calculates and reports; it does not send invites

## Inputs

| Field | Description | Example |
|-------|-------------|---------|
| `meeting_time` | Date and time of the proposed meeting | `"2025-06-10 14:00"` |
| `source_city` | City or IANA timezone where the time is given | `"New York"` or `"America/New_York"` |
| `cities` | Comma-separated list of target cities | `"London, Tokyo, Sydney, Beijing"` |

If the user forgets to provide `source_city`, ask before proceeding.
If the user omits the year, assume the current year.

## Step-by-step instructions

1. **Collect inputs** from the user's message. Extract `meeting_time`, `source_city`, and `cities`.
2. **Run the script** with the inputs:

```bash
python .agents/skills/meeting-time-planner/scripts/convert_meeting_time.py \
  --time "2025-06-10 14:00" \
  --source "New York" \
  --cities "London,Tokyo,Sydney,Beijing"
```

3. **Parse the JSON output** from the script. It returns a list of objects, one per city.
4. **Present the results** as a Markdown table (see Expected output format below).
5. **Add a brief recommendation** after the table: highlight the best overlap window, or flag that no overlap exists within working hours.
6. If any city has `holiday: true`, call that out explicitly so the user can decide whether to reschedule.

## Expected output format

Present a table like this:

| City | Local Time | Day | Working Hours? | Holiday? |
|------|-----------|-----|---------------|----------|
| New York | 14:00 Tue | Tue | Yes | No |
| London | 19:00 Tue | Tue | No (after 18:00) | No |
| Tokyo | 03:00 Wed | Wed | No (before 09:00) | No |
| Sydney | 04:00 Wed | Wed | No (before 09:00) | No |

After the table, write 1–3 sentences summarising the situation and suggesting the best alternative if no universal working-hours overlap exists.

## Important limitations

- Working hours are defined as Mon–Fri 09:00–18:00 local time. The script does not support custom hours; mention this if the user asks.
- Holiday data comes from the `holidays` Python package, which covers public holidays for ~100 countries. Regional/state holidays (e.g. US state holidays) are included where available.
- If the user provides an unrecognised city name, the script will print an error listing supported cities. Ask the user to pick a nearby supported city or provide an IANA timezone string directly.
- This skill handles one specific datetime at a time. For a range of possible slots, call the script once per candidate time.
