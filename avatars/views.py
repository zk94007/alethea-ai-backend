from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import PageNumberPagination
from avatars.models import Avatar
from avatars.serializer import AvatarSerializer
from users.permissions import CustomAdmin


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 10


class AvatarViewSet(ModelViewSet):
    queryset = Avatar.objects.all()
    serializer_class = AvatarSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Avatar.objects.prefetch_related("user").filter(user=self.request.user)
        else:
            return self.queryset

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[
            AllowAny,
        ],

    )
    def public(self, request):
        queryset = Avatar.objects.filter(is_public=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[
            CustomAdmin,
        ],
    )
    def admin(self, request):
        queryset = Avatar.objects.prefetch_related("user").all()
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
