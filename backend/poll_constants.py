"""Shared constants for the daily arXiv poller.

Kept in a single module so the scheduler, the migration script, and the
arXiv service agree on the same numbers. Import from here rather than
redefining locally.
"""

# On first run (no prior state), look back this many days. Bounded so we
# don't accidentally request 7 years of history against arXiv.
INITIAL_BACKFILL_DAYS = 14

# Always re-query one day before the last successful submittedDate to
# absorb same-day publications that arrived after our previous run.
REPOLL_OVERLAP_DAYS = 1

# Hard ceiling on papers returned from a single ``fetch_papers_since``
# call. Guards against runaway loops from malformed queries or a
# pathological date range. Under normal operation (daily poll, a handful
# of categories) we expect at most a few hundred results per call.
POLL_SAFETY_CAP = 10000

# Default categories scanned by the daily poll and the date-range backfill
# script. Lifted out of scheduler.py so scripts can import without dragging
# in BackgroundScheduler construction at module import.
DEFAULT_CATEGORIES = {
    "cs.AI", "cs.LG", "cs.CL", "cs.CV", "cs.RO",
    "cs.MA", "cs.NE", "cs.IR", "cs.SI", "cs.HC", "cs.CY",
}
