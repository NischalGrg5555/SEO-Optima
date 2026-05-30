# Dashboard (step-by-step)

Purpose
- Explain how the dashboard and analysis list/detail pages are built and how to add new widgets or reports.

Files involved
- [dashboard/views.py](dashboard/views.py)
- [dashboard/models.py](dashboard/models.py)
- [dashboard/urls.py](dashboard/urls.py)
- templates/dashboard/*
- services/ (pagespeed.py, pdf_generator.py, image_extractor.py, keyword_extractor.py)

Step-by-step implementation
1. Models
   - Store analysis records in `dashboard/models.py` (type, url, created_by, status, results JSON, is_deleted flags).
2. Views & URLs
   - List view: paginated list of analyses (filter by user, date, type). Implement in `dashboard/views.py` and route in `dashboard/urls.py`.
   - Detail view: shows analysis results, charts, and actions (re-run, download PDF, delete).
   - Use class-based views (`ListView`, `DetailView`) or function views depending on existing patterns.
3. Services
   - Extraction and analysis logic lives in `dashboard/services/*`. Keep views thin — call service functions that return structured results.
4. Templates & frontend
   - Build partials for analysis cards, result tables, and filters. Use existing `templates/dashboard/base.html` for layout.
   - Add client-side JS for asynchronous status updates when long-running analysis is executed.
5. Background/management commands
   - For long analyses, use Django management commands or background worker (Celery/RQ) to process and persist results. See `dashboard/management/commands` for examples.
6. PDF exports
   - Reuse `dashboard/services/pdf_generator.py` to create downloadable reports; expose a view that returns `HttpResponse` with `application/pdf`.
7. Tests
   - Add tests in `dashboard/tests.py` for list/detail views, service logic, and PDF generation.

How to run locally
- The dashboard runs in the main Django app; ensure media/static are collected and server started.

Extending
- To add a new analysis type: add model fields, new service in `dashboard/services/`, an entry point in views, template partial, and tests.
