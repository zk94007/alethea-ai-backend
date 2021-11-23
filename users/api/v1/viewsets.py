import os
import datetime

from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework import permissions, generics
from rest_framework.generics import UpdateAPIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
# from rest_framework_simplejwt import authentication
import json
from .serializers import BlockUnBlockUser, SignupSerializer, AllUserSerializer, UserSerializer
from users.models import Roles
from users.permissions import CustomAdmin

User = get_user_model()


class SignupViewSet(ModelViewSet):
    permission_classes = (permissions.AllowAny,)
    serializer_class = SignupSerializer
    # authentication_classes = [authentication.JWTAuthentication]
    authentication_classes = [BasicAuthentication]
    http_method_names = ["post", "options"]


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 10


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = StandardResultsSetPagination

    def get_queryset(self): 
        return User.objects.filter(pk=self.request.user.pk)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[
            CustomAdmin,
        ],
    )
    def admin(self, request):
        if request.GET.get("search"):
            queryset = User.objects.filter(email__icontains=request.GET.get("search")).annotate(
                is_verified=Exists(EmailAddress.objects.filter(user=OuterRef('pk'))))
        else:
            queryset = User.objects.all().annotate(
                is_verified=Exists(EmailAddress.objects.filter(user=OuterRef('pk'))))
        self.serializer_class = AllUserSerializer
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class BlockUser(UpdateAPIView):

    queryset = User.objects.all()
    serializer_class = BlockUnBlockUser
    permission_classes = (permissions.IsAdminUser,)
    http_method_names = ["patch"]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save()
        return Response({"detail": "User has been blocked"})


class UnBlockUser(BlockUser):
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = True
        instance.save()
        return Response({"detail": "User has been unblocked"})
