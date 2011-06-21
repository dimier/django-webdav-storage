import os
import httplib2
from django.core.files import File
from django.conf import settings
from django.utils import unittest
from django.test.client import Client
from .models import FileModel


def upload_file(self, name):
    post_data = {
        'testfile': open(os.path.join(os.path.dirname(__file__), name)),
    }
    return self.client.post('/upload/', post_data)


class WebDAVStorageTest(unittest.TestCase):
    def setUp(self):
        self.client = Client()
        response = upload_file(self, "test.png")
        self.assertEqual(response.status_code, 200)

        self.file_model_instance = FileModel.objects.all()[0]

    def tearDown(self):
        FileModel.objects.all().delete()
        self.file_model_instance = None

    def test_exists(self):
        f = self.file_model_instance.testfile
        file_name = f.name
        self.assertTrue(f.storage.exists(file_name))

    def test_size(self):
        self.assertEqual(self.file_model_instance.testfile.size, 482)

    def test_open(self):
        content = self.file_model_instance.testfile.read()
        self.assertEqual(len(content), 482)

    def test_delete(self):
        f = self.file_model_instance.testfile
        file_name = f.name
        f.delete()
        self.assertFalse(f.storage.exists(file_name))

    def test_url(self):
        http = httplib2.Http(timeout=5)
        response, response_body = http.request(self.file_model_instance.testfile.url)
        self.assertEqual(response.status, 200)

    def test_conflict_names(self):
        response = upload_file(self, "test.png")
        self.assertEqual(response.status_code, 200)
        f1, f2 = FileModel.objects.all()
        self.assertNotEqual(f1.testfile.name, f2.testfile.name)
