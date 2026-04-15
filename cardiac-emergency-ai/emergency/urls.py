from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("api/dashboard/", views.dashboard_api, name="dashboard_api"),
    path("api/report/<int:report_id>/", views.report_api, name="report_api"),
    path("upload/", views.upload_patient, name="upload"),
    path("processing/<uuid:patient_id>/", views.processing, name="processing"),
    path("process/<uuid:patient_id>/", views.run_pipeline_sync, name="run_pipeline"),
    path("report/<int:report_id>/", views.view_report, name="report"),
    path("confirm/<int:report_id>/", views.doctor_confirm, name="confirm"),
]

