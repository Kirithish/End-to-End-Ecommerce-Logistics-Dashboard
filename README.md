# End-to-End Ecommerce Logistics Dashboard

**Python + SQL Server + Power BI** | Author: Kirithish Kathiresan

An end-to-end analysis of last-mile ecommerce deliveries: data cleaning and feature engineering in Python, a star schema in SQL Server, and a 5-page Power BI dashboard that ends in a recommendation.

## Business question

Which conditions (traffic, time of day, distance, area type, weather and agent profile) make deliveries slow, how many minutes does each one add, and what would fixing the biggest one save?

## Key findings

All figures come from 43,739 deliveries. A delivery is **late** when it takes more than **160 minutes** (the 75th percentile). Overall, 76.95% of deliveries are on time (10,084 late) and the average delivery takes 125 minutes.

| Finding | Evidence |
|---|---|
| **Jam traffic is the biggest driver** | 41.0% of jam-traffic deliveries are late vs 6.0% in low traffic. Average time is about 148 min in a jam vs 101 min in low traffic, and the gap holds within the same distance band. |
| **Evenings are slowest** | Evening orders average about 140 min vs about 101 min in the morning. |
| **Long trips are late far more often** | Trips of 10 km or more are late about 38% of the time, vs 7 to 9% under 6 km. |
| **Low-rated agents are late more often** | Agents rated below 4.5 are late about 63% of the time vs 13 to 15% for higher-rated agents. |
| **City, weekday and weekend barely matter** | Average delivery time stays within about 123 to 129 min across cities, and weekdays and weekends are the same. |

### Recommendation

1. **Add evening capacity where traffic is heaviest.** Stagger pickups or add agents between about 5 and 10 pm.
2. **Route long trips deliberately.** Assign trips of 10 km or more to the nearest available agent and avoid batching them.
3. **Match agents to routes.** Pair coaching for agents rated below 4.5 with shorter, lower-traffic routes.

**Estimated impact (illustrative):** jam traffic accounts for about ₹259K of the ₹435K illustrative cost of late deliveries (about 59%). A 20% reduction would save an estimated **₹52K** over the 44 days in this data, under the assumed rates below.

## Dashboard (Power BI, Import mode)

Five pages: Overview, Delivery Performance, City Performance, Cost Analysis, and Drivers & Actions. Import mode was chosen because the data is static and the report is shared as a file; DirectQuery would suit data that updates continuously.

![Overview](Visual/Overview%20Page.png)
![Delivery Performance](Visual/Delivery%20Peformance%20Page.png)
![City Performance](Visual/City%20Performance%20Page.png)
![Cost Analysis](Visual/Cost%20Analysis%20Page.png)
![Drivers and Actions](Visual/Drivers%20and%20Actions%20Page.png)

## Architecture

```
Ecommerce Delivery Data.csv -> Python (clean + features) -> SQL Server (star schema) -> Power BI
```

| Step | What I did |
|---|---|
| Clean and enrich | Fixed types and text, flagged invalid values, built distance (km, from coordinates), time-of-day, bands, late flag and an estimated city |
| Store | Staging table, then a star schema: `fact_deliveries`, lookup tables for weather, traffic, vehicle, area, category, city and date, a separate `delivery_costs` table, and one analysis view (`vw_delivery_analysis`). See `Data/SQL Server Brief.png`. |
| Visualise | 5-page Power BI dashboard with DAX measures, in `Visual/End_to_End_Dashboard Pro.pbix` |

## Data

**Source:** Amazon Delivery Dataset (Kaggle), 43,739 deliveries from 11 Feb to 6 Apr 2022 in one flat table.

### Cleaning log

| Issue | Count | Handling |
|---|---|---|
| Zero or negative coordinates | 3,693 rows (8.4%) | Rows kept; distance blank and city set to Unknown |
| Agent ratings above 5 (6.0) | 53 | Set to blank |
| Agent ages under 18 (15) | 38 | Set to blank |
| Missing weather and traffic | 91 each | Labelled "Unknown" |
| Missing agent rating | 54 | Left blank |
| Text issues | n/a | Trimmed spaces, fixed "Metropolitian" typo |
| Pickup time crossing midnight | n/a | Moved to the next day |

### Limitations (please read)

- **Possibly simulated data.** Effects change in sharp steps at round numbers (rating 4.5, age 30, distance 10 km), and pickup wait is only ever 5, 10 or 15 minutes. Treat the findings as patterns in this dataset, not claims about real delivery operations.
- **Odd/even date pattern.** The late rate alternates between odd and even dates (about 16% vs 32%) because the traffic, time-of-day and distance mix differs. The main effects above hold within each group separately. I treat this as a data artifact and do not show a daily trend.
- **Only 44 days** inside a 55-day range (19 to 28 Feb and 22 Mar are missing), so there is no seasonality or month-over-month analysis.
- **No scheduled time, late flag, review scores, agent IDs or store IDs.** "Late" is my own threshold (over 160 minutes), and analysis is by group, not by individual agent.
- **City is estimated** from the nearest of 22 city centres to the store coordinates, so it is approximate.
- **Observational data:** findings show association, not proof of cause.
- **Small groups** (Semi-Urban with 152 rows, bicycle with 15) are not used for conclusions.

### Illustrative cost assumptions

The cost page uses assumed rates and is **not measured cost**: 0.5 INR per agent minute, a fuel cost per km by vehicle (motorcycle 2.5, scooter 2.0, van 7.0, bicycle 0), and a 25 INR penalty per late order. They are used only to turn real minute gaps into rupees.

## Repository structure

```
README.md
Data/
  Ecommerce Delivery Data.csv
  SQL Server Brief.png
Visual/
  Overview Page.png
  Delivery Peformance Page.png
  City Performance Page.png
  Cost Analysis Page.png
  Drivers and Actions Page.png
  End_to_End_Dashboard Pro.pbix
```

## How to reproduce

1. Load the dataset into SQL Server as a staging table (SSMS, Import Flat File), then build the star schema and the `vw_delivery_analysis` view.
2. Open the `.pbix` in Power BI Desktop and point the data source at your SQL Server instance and that view.

## Skills demonstrated

Python (pandas, feature engineering), SQL Server (star schema, keys, CTEs, window functions, views), Power BI (DAX, Import mode, sort-by-column, conditional formatting), data validation, and clear communication of limits.
