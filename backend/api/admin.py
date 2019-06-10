from django.contrib import admin

from .models import Attachment, Entity, EventDetails, EventParticipants, Post


class InlineAttachments(admin.StackedInline):
    """Inline attachments."""

    extra = 1
    model = Attachment


class InlineEventDatetime(admin.StackedInline):
    """Inline event."""

    model = EventDetails
    verbose_name = "Event datetime"
    verbose_name_plural = "Event datetime"


class InlineEventParticipants(admin.StackedInline):
    """Inline event particiants."""

    extra = 1
    model = EventParticipants
    verbose_name = "Event participants"
    verbose_name_plural = "Event participants"


@admin.register(Post)
class AdminPost(admin.ModelAdmin):
    """Post admin."""

    model = Post
    inlines = (
        InlineAttachments, InlineEventDatetime, InlineEventParticipants
    )
    readonly_fields = ('created', 'updated')


admin.site.register(Attachment)
admin.site.register(Entity)
admin.site.register(EventDetails)
admin.site.register(EventParticipants)
