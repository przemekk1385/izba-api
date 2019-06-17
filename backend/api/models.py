from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.html import escape
from markdownx.models import MarkdownxField

from .utils.uuid4path import Uuid4Path


CURRENT_DATE = datetime.now()

TYPES_ENTITIES = (
    (1, 'member'),
    (2, 'other'),
)


def no_unsafe(value):
    """Validate against unsafe characters."""
    if len(value) != len(escape(value)):
        raise ValidationError(
            'To pole zawiera niedozwolone znaki.',
        )


class Post(models.Model):
    """Post model."""

    title = models.CharField(max_length=100, validators=[no_unsafe])
    content = MarkdownxField()
    header = models.ImageField(blank=True, null=True, upload_to=Uuid4Path())
    slider = models.BooleanField(null=False, default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta."""

        ordering = ('created', )

    def __str__(self):
        """Model representation."""
        return "{}".format(self.title)


class Entity(models.Model):
    """Entity model."""

    name = models.CharField(max_length=100, validators=[no_unsafe])
    url = models.CharField(max_length=100, validators=[no_unsafe])
    image = models.ImageField(null=True, upload_to=Uuid4Path())
    type = models.IntegerField(choices=TYPES_ENTITIES)

    class Meta:
        """Meta."""

        verbose_name_plural = "Entities"

    def __str__(self):
        """Model representation."""
        return "{}".format(self.name)


class Attachment(models.Model):
    """Attachment model."""

    name = models.CharField(max_length=100, validators=[no_unsafe])
    file = models.FileField(upload_to=Uuid4Path())
    # relationships
    post = models.ForeignKey(Post, null=False, on_delete=models.CASCADE)

    def __str__(self):
        """Model representation."""
        return "{}".format(self.name)


class EventDetails(models.Model):
    """Event details model."""

    start = models.DateTimeField(blank=True)
    end = models.DateTimeField(blank=True)
    place = models.CharField(blank=True, max_length=100, null=True,
                             validators=[no_unsafe])
    # relationships
    post = models.OneToOneField(Post, null=False, on_delete=models.CASCADE)

    class Meta:
        """Meta."""

        verbose_name_plural = "Events details"

    def __str__(self):
        """Model representation."""
        return "{} - {}".format(self.start, self.end)

    def clean(self):
        """Validate datetime."""
        if self.start >= self.end:
            raise ValidationError(
                'Data końcowa musi być późniejsza niż początkowa.',
            )


class EventParticipants(models.Model):
    """Event participants model."""

    label = models.CharField(max_length=100, validators=[no_unsafe])
    # relationships
    entities = models.ManyToManyField(Entity)
    post = models.ForeignKey(Post, null=False, on_delete=models.CASCADE)

    class Meta:
        """Meta."""

        verbose_name_plural = "Events participants"

    def __str__(self):
        """Model representation."""
        return "{}".format(self.label)
