from django.db import models
from webdav_storage.backends import WebDAVStorage


storage = WebDAVStorage()


class FileModel(models.Model):
    testfile = models.FileField(upload_to="uploadtest/", storage=storage)
