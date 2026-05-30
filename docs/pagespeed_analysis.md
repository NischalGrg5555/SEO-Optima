# Pagespeed Analysis (step-by-step)

Purpose
- Document the pagespeed analysis feature: how to run it, where results are stored, and how to add checks.

Files involved
- [dashboard/services/pagespeed.py](dashboard/services/pagespeed.py)
- [dashboard/models.py](dashboard/models.py)
- [dashboard/views.py](dashboard/views.py)

Step-by-step implementation
1. Service
   - Implement API calls or Puppeteer/ Lighthouse wrapper in `dashboard/services/pagespeed.py` to fetch metrics.
   - Normalize returned results into a consistent dict with score, metrics, and suggested fixes.
2. Model storage
   - Persist the normalized result in an analysis record (JSONField) with metadata (URL, timestamp, analyzer version).
3. Triggering
   - Expose a view or management command that calls the service and stores the result. For heavy operations, run in background worker.
4. Display
   - In analysis detail template, render summary scores, metric breakdown, and recommended fixes.
5. Tests
   - Write unit tests mocking external API responses and asserting normalization logic.

Extending
- Add custom thresholds and alerts by adding columns/fields to models and checking them after analysis.
