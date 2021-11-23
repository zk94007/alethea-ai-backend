from django.urls import path

from . import views

urlpatterns = [
    path("", views.CategoriesViewList.as_view()),
    path("public/", views.GetPublicViewList.as_view()),
]
