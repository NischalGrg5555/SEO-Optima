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
]
