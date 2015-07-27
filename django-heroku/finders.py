from django.contrib.staticfiles.finders import FileSystemFinder
from django.core.files.storage import FileSystemStorage
from django.utils.datastructures import SortedDict
from django.conf import settings


class UploadMediaFinder(FileSystemFinder):
    """Find media files in UPLOAD_MEDIA_ROOT"""

    def __init__(self, apps=None, *args, **kwargs):
        self.locations = [
            ('', self._get_upload_media_location()),
        ]
        self.storages = SortedDict()

        filesystem_storage = FileSystemStorage(location=self.locations[0][1])
        filesystem_storage.prefix = self.locations[0][0]
        self.storages[self.locations[0][1]] = filesystem_storage

    def _get_upload_media_location(self):
        """Get bower components location"""
        path = settings.UPLOAD_MEDIA_ROOT
        return path


