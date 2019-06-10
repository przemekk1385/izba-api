import json

from django.shortcuts import get_object_or_404
from rest_framework import serializers
from markdownx.utils import markdownify

from .models import Attachment, Entity, EventDetails, EventParticipants, Post


class MarkdownField(serializers.Field):
    """Field containing markdown."""

    def to_representation(self, value):
        """Object instance to dict of primitive datatypes."""
        return markdownify(value)


class AttachmentsSerializer(serializers.ModelSerializer):
    """Entity serializer."""

    class Meta:
        """Meta."""

        fields = ('__all__')
        model = Attachment


class EntitiesSerializer(serializers.ModelSerializer):
    """Entity serializer."""

    class Meta:
        """Meta."""

        fields = ('__all__')
        model = Entity


class EventDetailsSerializer(serializers.ModelSerializer):
    """EventDetails serializer."""

    class Meta:
        """Meta."""

        fields = ('id', 'start', 'end', 'place')
        model = EventDetails


class EventParticipantsSerializer(serializers.ModelSerializer):
    """EventParticipants serializer."""

    class Meta:
        """Meta."""

        depth = 1
        fields = ('id', 'label', 'entities')
        model = EventParticipants


class PostsListSerializer(serializers.ModelSerializer):
    """Posts /list/ serializer for client and administration panel."""

    class Meta:
        """Meta."""

        depth = 1
        fields = ('id', 'title', 'header', 'slider', 'created', 'updated',
                  'eventdetails')
        model = Post


class PostsBaseSerializer(serializers.ModelSerializer):
    """Posts serializer for administration panel."""

    attachment_set = AttachmentsSerializer(many=True,
                                           required=False)
    eventdetails = EventDetailsSerializer(many=False,
                                          required=False)
    eventdetails_data = serializers.CharField(required=False)
    eventparticipants_set = EventParticipantsSerializer(many=True,
                                                        required=False)
    eventparticipants_set_data = serializers.CharField(required=False)

    class Meta:
        """Meta."""

        fields = ('__all__')
        model = Post

    def create(self, validated_data):
        """Create instance."""
        try:
            ed_data = json.loads(  # ed stands for eventdetails
                validated_data.pop('eventdetails_data')
            )
        except KeyError:
            ed_data = None
        try:
            ep_set_data = json.loads(  # ep stands for eventparticipants
                validated_data.pop('eventparticipants_set_data')
            )
        except KeyError:
            ep_set_data = []
        post = Post.objects.create(**validated_data)
        if ed_data:
            EventDetails.objects.create(post=post, **ed_data)
        for ep_data in ep_set_data:
            self._eventparticipants_create(post, ep_data)
        return post

    def update(self, post, validated_data):
        """Update instance."""
        # ed stands for eventdetails
        ed_data = self._pop_data(validated_data,
                                 'eventdetails_data')
        # ep stands for eventparticipants
        ep_set_data = self._pop_data(validated_data,
                                     'eventparticipants_set_data')
        self._object_update(post, validated_data)
        post.save()
        if ed_data:
            try:
                self._object_update(post.eventdetails, ed_data)
            except EventDetails.DoesNotExist:
                EventDetails.objects.create(post=post, **ed_data)
            else:
                post.eventdetails.save()
        if ep_set_data:
            ep_in_data = [ep['id'] for ep in ep_set_data if 'id' in ep.keys()]
            ep_in_base = post.eventparticipants_set.values_list('id',
                                                                flat=True)
            # handle deleted
            self._objects_delete(EventParticipants,
                                 set(ep_in_base).difference(ep_in_data))
            for ep_data in ep_set_data:
                try:
                    ep = EventParticipants.objects.get(id=ep_data['id'])
                except EventParticipants.DoesNotExist:  # faulty id - ignore
                    pass
                except KeyError:  # new entry - create
                    self._eventparticipants_create(post, ep_data)
                else:  # change entry
                    entities = self._entities_get_or_404(ep_data)
                    self._object_update(ep, ep_data)
                    # get ids from data and database
                    ep.entities.set(entities)
                    ep.save()
        return post

    def _entities_get_or_404(self, data):
        return [get_object_or_404(Entity, id=id)
                for id
                in self._pop_data(data, 'entities', default=[], JSON=False)]

    def _eventparticipants_create(self, post, ep_data):
        entities = self._entities_get_or_404(ep_data)
        ep = EventParticipants.objects.create(post=post, **ep_data)
        ep.entities.add(*entities)

    def _object_update(self, obj, data):
        for field in data.keys():
            setattr(obj, field, data[field])

    def _objects_delete(self, model, ids):
        for id in ids:
            try:
                model.objects.filter(id=id).delete()
            except model.DoesNotExist:  # ignore already deleted
                pass

    def _pop_data(self, dict, key, default={}, JSON=True):
        try:
            data = dict.pop(key)
        except KeyError:
            return default
        else:
            return json.loads(data) if JSON else data


class PostsMarkdownifySerializer(serializers.ModelSerializer):
    """Posts serializer for client."""

    content = MarkdownField(read_only=True)
    attachment_set = AttachmentsSerializer(many=True)
    eventdetails = EventDetailsSerializer(many=False)
    eventparticipants_set = EventParticipantsSerializer(many=True)

    class Meta:
        """Meta."""

        model = Post
        fields = ('__all__')
