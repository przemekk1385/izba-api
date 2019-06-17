from pathlib import Path
from uuid import uuid4

from django.utils.deconstruct import deconstructible


@deconstructible
class Uuid4Path(object):
    """Unique upload path."""

    def __call__(self, instance, filename):
        """Implement call operator."""
        return Path('{}.{}'.format(uuid4(),
                                   filename.split('.')[-1])).as_posix()
