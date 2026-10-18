# Water Saver Score Methodology Audit

The existing household and farmer score formulas remain in place. The pre-launch input fix treats an unreported household vehicle-washing frequency as missing for new assessments; an explicitly reported zero retains its existing adjustment. Saved scores and historical results are not recalculated.

## Limitations and future work

- **Three-way household split:** Keep estimated water consumption per person, conservation performance, and assessment completeness/data quality as separate concepts. Define and validate criteria before introducing a new performance score.
- **Farmer volume vs. practice separation:** Report estimated irrigation volume separately from reported irrigation practices. A meaningful crop-water or application-efficiency assessment needs agronomic and field data that are not currently collected.
- **Measured vs. estimated data capture:** Distinguish meter or flow measurements, user-provided estimates, and configured defaults. Current entered values are not necessarily measured.
- **Versioned scoring:** Version any future formula change and preserve existing stored scores with their original meaning; do not silently recalculate historical assessments.
