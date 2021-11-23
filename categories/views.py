from rest_framework import generics, permissions
from categories.models import Categories
from .serializer import CategoriesSerializer


class CategoriesViewList(generics.ListAPIView):
    queryset = Categories.objects.all().select_related("user")
    serializer_class = CategoriesSerializer

    def get_queryset(self):
        return Categories.objects.filter(user=self.request.user).select_related("user")


class GetPublicViewList(CategoriesViewList):
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        return Categories.objects.filter(is_public=True).select_related("user")
