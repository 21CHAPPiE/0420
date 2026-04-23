# Reservoir Event Timeseries Schema

## Source

This table is loaded from:

- [merged_all_en.csv](</D:/a_hydro/0420/reservoir_qa/CSV(1)/CSV/merged_all_en.csv>)

Target MySQL table:

- `reservoir_event_timeseries`

## Purpose

This table stores event-level time series rows from the merged CSV dataset so they can be queried later for numeric question answering.

## Columns

| Column | Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `BIGINT` | No | Auto-increment primary key |
| `reservoir_code` | `VARCHAR(64)` | No | Fixed reservoir code, currently `TANKENG` |
| `event_id` | `VARCHAR(32)` | No | Event identifier derived from the CSV filename without `.csv` |
| `observation_no` | `INT` | No | 1-based row number within each event CSV, used to preserve duplicate timestamps |
| `event_time` | `DATETIME` | No | Observation timestamp from CSV column `time` |
| `rainfall_mm` | `DECIMAL(10,4)` | Yes | Rainfall value from CSV column `prcp` |
| `water_level_m` | `DECIMAL(10,3)` | Yes | Water level value from CSV column `level` |
| `outflow_m3s` | `DECIMAL(12,3)` | Yes | Outflow value from CSV column `outflow` |
| `inflow_m3s` | `DECIMAL(12,3)` | Yes | Inflow value from CSV column `inflow` |
| `source_filename` | `VARCHAR(255)` | No | Original CSV filename with `.csv` suffix |
| `created_at` | `DATETIME` | No | Row creation timestamp |

## Keys and constraints

| Name | Type | Columns | Purpose |
| --- | --- | --- | --- |
| `PRIMARY KEY` | PK | `id` | Surrogate key |
| `uk_event_timeseries` | UNIQUE | `reservoir_code, event_id, observation_no` | Prevent duplicate import of the same row position |
| `idx_event_timeseries_time` | INDEX | `event_time` | Support time-range queries |
| `idx_event_timeseries_event_time` | INDEX | `event_id, event_time` | Support per-event time-series queries |

## Field mapping from CSV

| CSV column | Table column |
| --- | --- |
| `time` | `event_time` |
| `prcp` | `rainfall_mm` |
| `level` | `water_level_m` |
| `outflow` | `outflow_m3s` |
| `inflow` | `inflow_m3s` |
| `eventid` | `event_id` |

`observation_no` is generated during import and is not present in the CSV.

## Notes

- Blank numeric values are loaded as `NULL`.
- Rows with blank `time` are skipped during import.
- `source_filename` is reconstructed as `<event_id>.csv`.
- Duplicate timestamps within the same event are preserved because uniqueness is based on `observation_no`, not `event_time`.
