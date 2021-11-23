from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from users.permissions import CustomAdmin

from jobs.models import Job
from users.models import WidgetUserAccess
from jobs.serializer import JobSerializer


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 10


class JobViewSet(ModelViewSet):
    queryset = Job.objects.all().select_related("user")
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated, ]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Job.objects.filter(user=self.request.user).select_related("user")

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[
            CustomAdmin,
        ],
    )
    def admin(self, request):
        if request.GET.get("search"):
            queryset = Job.objects.select_related("user").filter(email__icontains=request.GET.get("search"))
        else:
            queryset = Job.objects.select_related("user").all()
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


def iframe_view(request):
    # print(request.META['HTTP_REFERER'])
    # allowed_host = request.META['HTTP_REFERER']
    # api_key = request.GET.get('api_key')
    character_id = request.GET.get('character')
    # access_object = WidgetUserAccess.objects.filter(allowed_host=allowed_host, api_key=api_key, is_active=True)
    final = """
            window.onload=function(){
            document.getElementById("widget_parent").innerHTML="<iframe id='frame_id' src='https://inft.alethea.ai/widget/""" + str(
        character_id) + """' border='0' allow='camera;microphone;display-capture;' style='height:100%;width:100%;margin:0;border:0;overflow:hidden;'></iframe>";};
            """
    return HttpResponse(final, content_type='application/x-javascript')
    # access_object = WidgetUserAccess.objects.filter(allowed_host=allowed_host, api_key=api_key, is_active=True)
    # if len(access_object):
    #     final = """
    #             window.onload=function(){
    #             document.getElementById("widget_block").innerHTML="<iframe id='frameId' src='https://inft.alethea.ai/widget/""" + str(character_id) + """' border='0' allow='camera *;microphone *;display-capture *;'></iframe>";};
    #             """
    #     return HttpResponse(final, content_type='application/x-javascript')
    # else:
    #     return HttpResponse(status=401)
