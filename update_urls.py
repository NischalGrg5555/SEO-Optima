#!/usr/bin/env python3
import os
os.chdir("/Users/nischalgurung/Desktop/Seo-optima v3")

# Read current urls.py
with open("dashboard/urls.py", "r") as f:
    content = f.read()

# Check if already added
if "pdf_report" in content:
    print("PDF report URLs already added!")
    exit(0)

# Find the imports section and update it
old_imports = """from .views import (
    dashboard_home,
    page_speed_insights,
    analysis_detail,
    AnalysisListView,
    delete_analysis,
    extract_headers_view,
    image_alt_finder,
    image_alt_list,
    image_alt_detail,
    delete_image_alt_analysis,
    keywords_finder,
    keywords_list,
    keywords_detail,
    delete_keyword_analysis,
    connect_gsc,
    gsc_callback,
    disconnect_gsc,
)"""

new_imports = """from .views import (
    dashboard_home,
    page_speed_insights,
    analysis_detail,
    AnalysisListView,
    delete_analysis,
    extract_headers_view,
    image_alt_finder,
    image_alt_list,
    image_alt_detail,
    delete_image_alt_analysis,
    keywords_finder,
    keywords_list,
    keywords_detail,
    delete_keyword_analysis,
    connect_gsc,
    gsc_callback,
    disconnect_gsc,
)
from .pdf_report_views import (
    pdf_reports_list,
    generate_pdf_report,
    pdf_report_detail,
    download_pdf_report,
    delete_pdf_report,
    regenerate_pdf_report,
)"""

content = content.replace(old_imports, new_imports)

# Find the urlpatterns and add new ones
old_patterns_end = """    # Google Search Console OAuth
    path("connect-gsc/", connect_gsc, name="connect_gsc"),
    path("gsc-callback/", gsc_callback, name="gsc_callback"),
    path("disconnect-gsc/", disconnect_gsc, name="disconnect_gsc"),
]"""

new_patterns_end = """    # Google Search Console OAuth
    path("connect-gsc/", connect_gsc, name="connect_gsc"),
    path("gsc-callback/", gsc_callback, name="gsc_callback"),
    path("disconnect-gsc/", disconnect_gsc, name="disconnect_gsc"),
    
    # PDF Reports
    path("reports/", pdf_reports_list, name="pdf_reports_list"),
    path("reports/generate/", generate_pdf_report, name="generate_pdf_report"),
    path("reports/<int:pk>/", pdf_report_detail, name="pdf_report_detail"),
    path("reports/<int:pk>/download/", download_pdf_report, name="download_pdf_report"),
    path("reports/<int:pk>/delete/", delete_pdf_report, name="delete_pdf_report"),
    path("reports/<int:pk>/regenerate/", regenerate_pdf_report, name="regenerate_pdf_report"),
]"""

content = content.replace(old_patterns_end, new_patterns_end)

# Write back
with open("dashboard/urls.py", "w") as f:
    f.write(content)

print("PDF report URLs added successfully!")
