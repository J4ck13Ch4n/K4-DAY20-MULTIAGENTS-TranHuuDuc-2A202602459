---
name: ensure-csv-format
description: Use this skill to confirm that CSV outputs adhere to the specified format and conventions.
---
- Open the CSV file intended for output.
- Check that the header matches the required format (e.g., order_id,timestamp_utc,region,amount_cents).
- Ensure that each row contains one entry per distinct order with a known amount.
- Verify that the timestamp is formatted as YYYY-MM-DDTHH:MM:SSZ (UTC).
- Confirm that the region names are in canonical spelling (North, South, East, West).
- Check that monetary values are represented in integer cents.
- If any discrepancies are found, correct them before finalizing the CSV output.
