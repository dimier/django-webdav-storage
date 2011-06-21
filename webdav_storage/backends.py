import urlparse
import httplib2
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.conf import settings as django_settings
from django.utils.encoding import filepath_to_uri
from webdav_storage import settings as default_settings


class ExtendedSettings(object):
    def __init__(self, app_settings, django_settings):
        self.app_settings = app_settings
        self.django_settings = django_settings

    def __getattr__(self, name):
        try:
            return getattr(self.django_settings, name)
        except AttributeError:
            return getattr(self.app_settings, name)


settings = ExtendedSettings(django_settings=django_settings, app_settings=default_settings)


class HTTPError(IOError):
    pass

class NotFound(HTTPError):
    pass


class WebDAVStorage(Storage):
    def __init__(self, public_host=None, dav_host=None, scheme=None, base_url=None, timeout=None):
        """
        If dav_host is None than public_host is used. Scheme defines http or
        https protocol being used for public urls.
        """
        if public_host is None:
            public_host = settings.WEBDAV_PUBLIC_HOST
        self.public_host = public_host
        self.dav_host = dav_host or public_host
        self.scheme = scheme or "http"
        self.base_url = base_url or django_settings.MEDIA_URL

        if timeout is None:
            timeout = settings.WEBDAV_TIMEOUT
        self.timeout = timeout

    def _get_url(self, name, public=False):
        """
        Gets url for the file specified by name. Public argument defines that
        public_host or dav_host is used.
        """
        if public:
            scheme = self.scheme
            host = self.public_host
        else:
            scheme = "http"
            host = self.dav_host
        return urlparse.urljoin("%s://%s%s" % (scheme, host, self.base_url), filepath_to_uri(name))

    def _construct_http(self):
        return httplib2.Http(timeout=self.timeout)

    def _head(self, name):
        url = self._get_url(name)
        http = self._construct_http()
        response, response_body = http.request(url, "HEAD")
        if response.status >= 400 and response.status != 404:
            raise HTTPError("HEAD", url, response.status)
        return response

    def url(self, name):
        return self._get_url(name, public=True)

    def exists(self, name):
        response = self._head(name)
        return response.status == 200

    def size(self, name):
        response = self._head(name)
        if response.status == 404:
            raise NotFound(self._get_url(name))

        try:
            return int(response["content-length"])
        except (KeyError, ValueError):
            raise HTTPError('Invalid or missing content length for %s: "%s"' % (name, response.get("content-length")))

    def _open(self, name, mode="rb"):
        if mode != "rb":
            raise IOError('Illegal mode "%s". Only "rb" is supported.' % (mode, ))
        url = self._get_url(name)
        http = self._construct_http()
        response, response_body = http.request(url, 'GET')
        if response.status >= 400:
            raise HTTPError('GET', url, response.status)
        return ContentFile(response_body)

    def delete(self, name):
        url = self._get_url(name)
        http = self._construct_http()
        response, response_body = http.request(url, 'DELETE')
        if response.status >= 400 and response.status != 404:
            raise HTTPError('DELETE', url, response.status)

    def _save(self, name, content):
        url = self._get_url(name)
        http = self._construct_http()
        content.seek(0)
        body = content.read()

        response, response_body = http.request(url, 'PUT', body=body, headers={'Content-type': 'application/octet-stream'})
        if response.status >= 400:
            raise HTTPError('PUT', url, response.status)
        return name
