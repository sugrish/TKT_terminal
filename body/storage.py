import json
import mimetypes
import posixpath
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible


@deconstructible
class SupabaseStorage(Storage):
    """Store uploaded files in a public Supabase Storage bucket."""

    def __init__(self, url=None, key=None, bucket=None, timeout=20):
        self.base_url = (url or settings.SUPABASE_URL).rstrip('/')
        self.key = key or settings.SUPABASE_KEY
        self.bucket = bucket or settings.SUPABASE_STORAGE_BUCKET
        self.timeout = timeout

    def _object_url(self, name, public=False):
        prefix = 'object/public' if public else 'object'
        return f'{self.base_url}/storage/v1/{prefix}/{self.bucket}/{quote(name)}'

    def _request(self, method, url, data=None, headers=None):
        request_headers = {
            'apikey': self.key,
            'Authorization': f'Bearer {self.key}',
        }
        request_headers.update(headers or {})
        request = Request(url, data=data, headers=request_headers, method=method)
        return urlopen(request, timeout=self.timeout)

    def _save(self, name, content):
        content.seek(0)
        content_type = (
            getattr(content, 'content_type', None)
            or mimetypes.guess_type(name)[0]
            or 'application/octet-stream'
        )
        try:
            self._request(
                'POST',
                self._object_url(name),
                data=content.read(),
                headers={'Content-Type': content_type, 'x-upsert': 'false'},
            ).close()
        except HTTPError as error:
            detail = error.read().decode(errors='replace')
            raise OSError(f'Supabase upload failed ({error.code}): {detail}') from error
        return name

    def _open(self, name, mode='rb'):
        with self._request('GET', self._object_url(name)) as response:
            return ContentFile(response.read(), name=name)

    def get_available_name(self, name, max_length=None):
        # A random suffix avoids a network round trip per exists() check.
        directory, filename = posixpath.split(name.replace('\\', '/'))
        stem, extension = posixpath.splitext(filename)
        unique_name = posixpath.join(directory, f'{stem}-{uuid.uuid4().hex[:8]}{extension}')
        return super().get_available_name(unique_name, max_length=max_length)

    def exists(self, name):
        try:
            self._request('HEAD', self._object_url(name, public=True)).close()
        except URLError:
            return False
        return True

    def delete(self, name):
        if not name:
            return
        self._request(
            'DELETE',
            f'{self.base_url}/storage/v1/object/{self.bucket}',
            data=json.dumps({'prefixes': [name]}).encode(),
            headers={'Content-Type': 'application/json'},
        ).close()

    def url(self, name):
        return self._object_url(name, public=True)
