from django.urls import include, path

from .router import router
from .views import UploadView


urlpatterns = [
    path('', include(router.urls)),
    path('upload/', UploadView.as_view()),
]
