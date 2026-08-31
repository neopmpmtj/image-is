from django.urls import path

from image_is import views

app_name = "image_is"

urlpatterns = [
    path("", views.HistoryView.as_view(), name="history"),
    path("new/", views.NewAnalysisView.as_view(), name="new"),
    path("analysis/<uuid:analysis_id>/", views.DetailView.as_view(), name="detail"),
]
