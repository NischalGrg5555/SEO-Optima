from django.urls import path
from .views import (
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

app_name = "dashboard"

urlpatterns = [
    path("", dashboard_home, name="home"),
    path("page-speed-insights/", page_speed_insights, name="page_speed_insights"),
    path("analysis/<int:pk>/", analysis_detail, name="analysis_detail"),
    path("analyses/", AnalysisListView.as_view(), name="analysis_list"),
    path("analysis/<int:pk>/delete/", delete_analysis, name="delete_analysis"),
    path("extract-headers/", extract_headers_view, name="extract_headers"),
    path("image-alt-finder/", image_alt_finder, name="image_alt_finder"),
    path("image-alt-analyses/", image_alt_list, name="image_alt_list"),
    path("image-alt-analysis/<int:pk>/", image_alt_detail, name="image_alt_detail"),
    path("image-alt-analysis/<int:pk>/delete/", delete_image_alt_analysis, name="delete_image_alt_analysis"),
    path("keywords-finder/", keywords_finder, name="keywords_finder"),
    path("keywords-analyses/", keywords_list, name="keywords_list"),
    path("keywords-analysis/<int:pk>/", keywords_detail, name="keywords_detail"),
    path("keywords-analysis/<int:pk>/delete/", delete_keyword_analysis, name="delete_keyword_analysis"),
    # Google Search Console OAuth
    path("connect-gsc/", connect_gsc, name="connect_gsc"),
    path("gsc-callback/", gsc_callback, name="gsc_callback"),
    path("disconnect-gsc/", disconnect_gsc, name="disconnect_gsc"),
]
