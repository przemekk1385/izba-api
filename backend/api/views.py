from pathlib import Path

from django.core.files.storage import default_storage
from rest_framework import status, views, viewsets
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .models import Attachment, Entity, Post, TYPES_ENTITIES
from .serializers import (AttachmentsSerializer,
                          EntitiesSerializer,
                          PostsSerializer,
                          PostsSerializerList,
                          PostsSerializerMarkdownifyContent,
                          PostsSerializerUseUploadedHeader)


class _Choices(object):

    __slots__ = (
        '_choices',
    )

    def __init__(self, choices):
        self._choices = choices

    @property
    def values(self):
        return [c[1] for c in self._choices]

    def key(self, value):
        try:
            return [c[0] for c in self._choices if c[1] == value][0]
        except IndexError:
            return -1


class UploadView(views.APIView):
    """API endpoint for file upload."""

    parser_classes = (MultiPartParser, )

    def put(self, request, format=None):
        """PUT method."""
        file_obj = request.data['file']
        filename = Path('tmp') / '{}'.format(file_obj.name)
        with default_storage.open(filename.as_posix(), 'wb+') as destination:
            for chunk in file_obj.chunks():
                destination.write(chunk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AttachmentsViewset(viewsets.ModelViewSet):
    """API endpoint for attachments."""

    queryset = Attachment.objects.all()
    serializer_class = AttachmentsSerializer

    def get_queryset(self):
        """Filtering."""
        qs = super().get_queryset()
        id = 0
        try:
            id = int(self.request.query_params.get('post'))
        except (TypeError, ValueError):
            pass
        return qs.filter(post=id) if id and self.action == 'list' else qs


class EntitiesViewset(viewsets.ModelViewSet):
    """API endpoint for entities."""

    queryset = Entity.objects.all().order_by('name')
    serializer_class = EntitiesSerializer

    def get_queryset(self):
        """Filtering."""
        choices = _Choices(TYPES_ENTITIES)
        qs = super().get_queryset()
        type = str(self.request.query_params.get('type')).lower()
        return qs.filter(type=choices.key(type)) if type in choices.values\
            else qs


class PostsViewset(viewsets.ModelViewSet):
    """API endpoint for posts."""

    queryset = Post.objects.all().order_by('-id')

    def get_serializer_class(self):
        """Pick serializer class."""
        if self.action == 'list':
            serializer = PostsSerializerList
        else:
            if self.request.data.get('header', None)\
                and isinstance(self.request.data['header'],
                               str):
                serializer = PostsSerializerUseUploadedHeader
            elif 'markdownify' in self.request.query_params:
                serializer = PostsSerializerMarkdownifyContent
            else:
                serializer = PostsSerializer
        return serializer

    def get_queryset(self):
        """Filtering."""
        qs = super().get_queryset()
        only = str(self.request.query_params.get('only')).lower()
        fs = {  # filters
            'events': {'eventdetails__isnull': False},
            'posts': {'eventdetails__isnull': True},
        }
        return qs.filter(**fs[only]).order_by('-id')\
            if only in fs.keys()\
            else qs.order_by('-id')
