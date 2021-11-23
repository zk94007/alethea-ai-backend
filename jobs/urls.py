from django.urls import path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("", views.JobViewSet)

urlpatterns = [
    path("inft/", views.iframe_view)
]

urlpatterns += router.urls
