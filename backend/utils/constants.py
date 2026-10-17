"""
AquaWise Water-Use Assumptions.

All values here are ESTIMATES based on commonly cited household water-use data.
They do NOT represent exact measurements for every situation.

These constants are deliberately centralised so the development team can update
them in one place if better reference data becomes available.  The application
must never present these values to the user as scientifically exact figures —
always use phrasing such as "estimated based on typical usage assumptions".

Sources consulted for the initial values:
  - World Health Organisation drinking-water guidelines
  - Bureau of Indian Standards domestic water requirements
  - Generic plumbing flow-rate data (standard residential fittings)

Assumptions are grouped by category and annotated with their unit and rationale.
"""

# ---------------------------------------------------------------------------
# BATHING / SHOWER
# ---------------------------------------------------------------------------

# Litres discharged per minute through a typical shower head.
# A standard residential shower head in India discharges roughly 8–12 L/min.
# We use 9 L/min as a conservative mid-range estimate.
SHOWER_FLOW_RATE_LPM = 9.0          # litres per minute

# Average volume for a bucket bath (a common alternative to a shower).
# A typical bucket holds 15–20 L; we use 18 L.
BUCKET_BATH_VOLUME_L = 18.0         # litres per bath

# ---------------------------------------------------------------------------
# TOILET
# ---------------------------------------------------------------------------

# Volume used by a standard (single-flush) toilet per flush.
# Most standard cisterns in Indian homes hold around 6 L.
TOILET_FLUSH_STANDARD_L = 6.0       # litres per flush

# Volume for a water-efficient dual-flush toilet (full flush).
TOILET_FLUSH_EFFICIENT_L = 3.0      # litres per flush

# Default used when toilet type is unknown.
TOILET_FLUSH_DEFAULT_L = 6.0        # litres per flush

# ---------------------------------------------------------------------------
# LAUNDRY
# ---------------------------------------------------------------------------

# Water used per laundry load.
# A front-loading washing machine uses ~45–55 L; a top-loader ~80–110 L.
# We use 60 L as a reasonable blended average for Indian homes where both
# types are common.
LAUNDRY_WATER_PER_LOAD_L = 60.0     # litres per load

# ---------------------------------------------------------------------------
# KITCHEN / DISHWASHING
# ---------------------------------------------------------------------------

# Litres flowing from an open kitchen tap per minute.
# Standard kitchen taps in India are typically 6–8 L/min.
KITCHEN_TAP_FLOW_RATE_LPM = 6.0     # litres per minute

# Water used by a dishwasher per cycle (where applicable).
DISHWASHER_WATER_PER_CYCLE_L = 14.0 # litres per cycle

# ---------------------------------------------------------------------------
# VEHICLE WASHING
# ---------------------------------------------------------------------------

# Water used when washing a vehicle with a running garden hose.
# A garden hose at typical pressure delivers ~15–20 L/min.
# A 10-minute wash ~ 150–200 L.  We use 150 L.
VEHICLE_WASH_HOSE_L = 150.0         # litres per wash (hose)

# Water used when washing a vehicle using a bucket and cloth.
# Two 15-L buckets is common practice; we use 30 L.
VEHICLE_WASH_BUCKET_L = 30.0        # litres per wash (bucket)

# Water used by a pressure washer vehicle wash.
VEHICLE_WASH_PRESSURE_WASHER_L = 60.0  # litres per wash (pressure washer)

# Default (when method is not specified).
VEHICLE_WASH_DEFAULT_L = 100.0      # litres per wash (default/unknown method)

# ---------------------------------------------------------------------------
# GARDENING / WATERING
# ---------------------------------------------------------------------------

# Litres discharged per minute through a garden hose for outdoor watering.
GARDENING_HOSE_FLOW_RATE_LPM = 15.0        # litres per minute
GARDENING_SPRINKLER_FLOW_RATE_LPM = 12.0   # litres per minute
GARDENING_DRIP_FLOW_RATE_LPM = 4.0         # litres per minute
GARDENING_BUCKET_FLOW_RATE_LPM = 8.0       # litres per minute (effective rate)

# Default when method is unspecified.
GARDENING_DEFAULT_FLOW_RATE_LPM = 12.0     # litres per minute

# ---------------------------------------------------------------------------
# REFERENCE POINT: DAILY PER-CAPITA WATER USE
# ---------------------------------------------------------------------------

# Product reference for the household score, not an individual target or
# universal measure of the right amount of household use.
# Reference: CPHEEO (Central Public Health and Environmental Engineering
# Organisation) recommends 135–150 L per capita per day for urban India.
BENCHMARK_HOUSEHOLD_LPCD = 150.0    # litres per capita per day

# A simple upper limit: above this per-capita consumption is flagged as high.
HIGH_CONSUMPTION_THRESHOLD_LPCD = 200.0  # litres per capita per day

# Percentage of total daily consumption above which a single category is
# flagged as a major consumer and triggers a recommendation.
HIGH_CATEGORY_SHARE_PERCENT = 30.0  # %

# ---------------------------------------------------------------------------
# WEEKLY / MONTHLY CONVERSION FACTORS
# ---------------------------------------------------------------------------

DAYS_IN_WEEK = 7
DAYS_IN_MONTH = 30

# Version 2 household assessment defaults. Values are configurable product
# assumptions, not universal household benchmarks. Results disclose every
# default used. Replace these with locally validated values where available.
HOUSEHOLD_ASSESSMENT_DEFAULTS = {
    "shower_flow_lpm": SHOWER_FLOW_RATE_LPM,
    "bucket_capacity_l": BUCKET_BATH_VOLUME_L,
    "toilet_flush_l": {
        "standard": TOILET_FLUSH_STANDARD_L,
        "dual_flush": TOILET_FLUSH_EFFICIENT_L,
        "low_flow": TOILET_FLUSH_EFFICIENT_L,
        "unknown": TOILET_FLUSH_DEFAULT_L,
    },
    "tap_flow_lpm": KITCHEN_TAP_FLOW_RATE_LPM,
    "dishwasher_l_per_cycle": DISHWASHER_WATER_PER_CYCLE_L,
    "machine_laundry_l_per_load": LAUNDRY_WATER_PER_LOAD_L,
    "hose_flow_lpm": GARDENING_HOSE_FLOW_RATE_LPM,
    "sprinkler_flow_lpm": GARDENING_SPRINKLER_FLOW_RATE_LPM,
    "drip_flow_lpm": GARDENING_DRIP_FLOW_RATE_LPM,
    "shower_scenario_reduction_minutes": 1.0,
}
