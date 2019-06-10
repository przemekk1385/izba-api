from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'attachments', views.AttachmentsViewset)
router.register(r'entities', views.EntitiesViewset)
router.register(r'posts', views.PostsViewset)
