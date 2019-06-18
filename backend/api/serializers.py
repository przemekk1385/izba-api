from pathlib import Path
import io
import mimetypes

from django.conf import settings
from django.db import IntegrityError
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework import serializers
from markdownx.utils import markdownify

from .models import Attachment, Entity, EventDetails, EventParticipants, Post


class MarkdownField(serializers.Field):
    """Field containing markdown."""

    def to_representation(self, value):
        """Object instance to dict of primitive datatypes."""
        return markdownify(value)


class AttachmentsSerializer(serializers.ModelSerializer):
    """Attachments serializer."""

    class Meta:
        """Meta."""

        fields = ('__all__')
        model = Attachment


class EntitiesSerializer(serializers.ModelSerializer):
    """Entities serializer."""

    class Meta:
        """Meta."""

        fields = ('__all__')
        model = Entity


class EventDetailsSerializer(serializers.ModelSerializer):
    """EventDetails serializer."""

    class Meta:
        """Meta."""

        fields = ('start', 'end', 'place')
        model = EventDetails
        read_only_fields = ('post', )


class EventParticipantsSerializer(serializers.ModelSerializer):
    """EventParticipants serializer."""

    id = serializers.IntegerField(required=False)

    class Meta:
        """Meta."""

        fields = ('id', 'label', 'entities')
        model = EventParticipants
        read_only_fields = ('post', )


class PostsSerializer(serializers.ModelSerializer):
    """Posts serializer for administration panel."""

    attachment_set = AttachmentsSerializer(many=True,
                                           read_only=True)
    eventdetails = EventDetailsSerializer(many=False,
                                          required=False)
    eventparticipants_set = EventParticipantsSerializer(many=True,
                                                        required=False)

    class Meta:
        """Meta."""

        fields = ('__all__')
        model = Post

    def create(self, validated_data):
        """Create instance."""
        eventdetails = validated_data\
            .pop('eventdetails', {})
        eventparticipants_set = validated_data\
            .pop('eventparticipants_set', [])
        post_instance = Post.objects.create(**validated_data)
        try:
            EventDetails.objects.create(post=post_instance,
                                        **eventdetails)
        except IntegrityError:
            pass  # seems there is no eventdetails
        for eventparticipants in eventparticipants_set:
            entities = eventparticipants.pop('entities')
            ep = EventParticipants.objects.create(post=post_instance,
                                                  **eventparticipants)
            ep.entities.add(*entities)
        return post_instance

    def update(self, post_instance, validated_data):
        """Update instance."""
        eventdetails = validated_data\
            .pop('eventdetails', {})
        eventparticipants_set = validated_data\
            .pop('eventparticipants_set', [])
        post_instance.title = validated_data.get('title',
                                                 post_instance.title)
        post_instance.content = validated_data.get('content',
                                                   post_instance.content)
        post_instance.header = validated_data.get('header',
                                                  post_instance.header)
        post_instance.slider = validated_data.get('slider',
                                                  post_instance.slider)
        post_instance.save()
        try:
            eventdetails_instance = post_instance.eventdetails
        except EventDetails.DoesNotExist:
            try:
                EventDetails.objects.create(post=post_instance,
                                            **eventdetails)
            except IntegrityError:
                pass  # seems there is no eventdetails
        else:
            eventdetails_instance.start = eventdetails\
                .get('start', eventdetails_instance.start)
            eventdetails_instance.end = eventdetails\
                .get('end', eventdetails_instance.end)
            eventdetails_instance.place = eventdetails\
                .get('place', eventdetails_instance.place)
            eventdetails_instance.save()
        # deleted eventparticipants
        for id in set(
            post_instance.eventparticipants_set.values_list('id',
                                                            flat=True)
        ).difference([
            ep['id'] for ep in eventparticipants_set if 'id' in ep.keys()
        ]):
            EventParticipants.objects.filter(id=id).delete()
        # added / updated eventparticipants
        for ep in eventparticipants_set:  # ep stands for eventparticipants
            entities = ep.pop('entities', [])
            try:
                ep_instance = EventParticipants.objects.get(id=ep['id'])
            except KeyError:  # new entry - create
                ep_instance = EventParticipants\
                    .objects\
                    .create(post=post_instance, **ep)
                ep_instance.entities.add(*entities)
            else:  # change entry
                ep_instance.label = ep.get('label',
                                           ep_instance.label)
                ep_instance.entities.set(entities)
                ep_instance.save()
        return post_instance


class PostsSerializerMarkdownifyContent(PostsSerializer):
    """Posts serializer for client."""

    content = MarkdownField(read_only=True)


class PostsSerializerUseUploadedHeader(PostsSerializer):
    """Posts serializer for already uploaded header."""

    header = serializers.CharField()

    def _to_inmemoryuploadedfile(self, validated_data):
        with open((Path(settings.MEDIA_ROOT)
                   / 'tmp'
                   / validated_data['header']).as_posix(),
                  'rb') as image:
            uploaded_image = InMemoryUploadedFile(
                file=io.BytesIO(image.read()),
                field_name=None,
                name=validated_data['header'],
                content_type=mimetypes.guess_type(validated_data['header']),
                size=image.tell(),
                charset=None
            )
            validated_data.update({
                    'header': uploaded_image,
            })
        Path(image.name).unlink()
        return validated_data

    def create(self, validated_data):
        """Create instance."""
        return super(self.__class__, self)\
            .create(self._to_inmemoryuploadedfile(validated_data))

    def update(self, post_instance, validated_data):
        """Update instance."""
        return super(self.__class__, self)\
            .update(post_instance,
                    self._to_inmemoryuploadedfile(validated_data))


class PostsSerializerList(serializers.ModelSerializer):
    """Posts /list/ serializer for client and administration panel."""

    class Meta:
        """Meta."""

        depth = 1
        fields = ('id', 'title', 'header', 'slider', 'created', 'updated',
                  'eventdetails')
        model = Post
