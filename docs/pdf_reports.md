# PDF Reports (step-by-step)

Purpose
- Explain how PDF report generation is implemented, including template selection and PDF renderer usage.

Files involved
- [dashboard/services/pdf_generator.py](dashboard/services/pdf_generator.py)
- [dashboard/pdf_report_views.py](dashboard/pdf_report_views.py)

Step-by-step implementation
1. Templates
   - Create HTML templates for PDF layout (use the same base CSS as site but keep print-friendly styles).
2. Renderer
   - Use `pdf_generator.py` to render HTML to PDF (we use wkhtmltopdf / WeasyPrint / headless Chrome depending on dependencies).
3. Data
   - Pass analysis result context into templates and render to PDF bytes.
4. Views
   - Expose a view that returns `HttpResponse` with `Content-Type: application/pdf` and proper `Content-Disposition` headers.
5. Storage
   - Optionally persist generated PDFs to `media/reports/` and serve via authenticated endpoints.
6. Tests
   - Render a small HTML fixture to PDF and assert the response content-type and non-empty content.

Extending
- Add templated sections for client branding (logo, contact info) and bulk-report generation.
