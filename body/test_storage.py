import json
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from .storage import SupabaseStorage


class SupabaseStorageTests(SimpleTestCase):
    def setUp(self):
        self.storage = SupabaseStorage(
            url='https://project.supabase.co',
            key='service-role-secret',
            bucket='employee-photos',
        )

    @patch('body.storage.urlopen')
    def test_url_requests_one_hour_signed_url(self, urlopen):
        response = Mock()
        response.read.return_value = json.dumps(
            {'signedURL': '/object/sign/employee-photos/employee_photos/photo.jpg?token=abc'}
        ).encode()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        urlopen.return_value = response

        url = self.storage.url('employee_photos/photo.jpg')

        self.assertEqual(
            url,
            'https://project.supabase.co/storage/v1/object/sign/'
            'employee-photos/employee_photos/photo.jpg?token=abc',
        )
        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_header('Authorization'), 'Bearer service-role-secret')
        self.assertEqual(request.get_header('Apikey'), 'service-role-secret')
        self.assertEqual(json.loads(request.data), {'expiresIn': 3600})

    @patch('body.storage.urlopen')
    def test_exists_uses_authenticated_private_object_endpoint(self, urlopen):
        response = Mock()
        urlopen.return_value = response

        self.assertTrue(self.storage.exists('employee_photos/photo.jpg'))

        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            'https://project.supabase.co/storage/v1/object/'
            'employee-photos/employee_photos/photo.jpg',
        )
        self.assertEqual(request.get_method(), 'HEAD')
