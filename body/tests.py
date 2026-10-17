import tempfile

from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Body_signup, PositionPermission

TEST_PASSWORD = 'Uncommon-Passphrase-2026!'


class SignupViewTests(TestCase):
    def test_root_url_redirects_to_body_signup(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/body/')

    def test_signup_page_is_available(self):
        response = self.client.get(reverse('body:signup'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign up')

    def test_valid_signup_creates_and_displays_employee_id(self):
        response = self.client.post(
            reverse('body:signup'),
            {
                'name': 'Alex Example',
                'age': 30,
                'department': 'Operations',
                'position': 'Coordinator',
                'residence': 'Example City',
                'gender': 'Other',
                'complications': 'None',
                'password': TEST_PASSWORD,
                'password_confirm': TEST_PASSWORD,
            },
            follow=True,
        )

        employee = Body_signup.objects.get()
        expected_id = f'COORDINATOR-OPERATIONS-AE-{timezone.localdate().year}'
        self.assertRedirects(response, reverse('body:signup_success'))
        self.assertEqual(employee.employee_id, expected_id)
        self.assertContains(response, 'Alex Example')
        self.assertContains(response, 'Operations')
        self.assertContains(response, expected_id)

    def test_homepage_displays_current_employee_profile(self):
        signup_data = {
            'name': 'Alex Example',
            'age': 30,
            'department': 'Operations',
            'position': 'Coordinator',
            'residence': 'Example City',
            'gender': 'Other',
            'complications': 'None',
            'password': TEST_PASSWORD,
            'password_confirm': TEST_PASSWORD,
        }
        self.client.post(reverse('body:signup'), signup_data)

        response = self.client.get(reverse('body:index'))
        employee = Body_signup.objects.get()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Alex Example')
        self.assertContains(response, 'Operations')
        self.assertContains(response, employee.employee_id)
        self.assertContains(response, 'No profile photo uploaded')

    def test_duplicate_employee_entry_is_rejected(self):
        signup_data = {
            'name': 'Alex Example',
            'age': 30,
            'department': 'Operations',
            'position': 'Coordinator',
            'residence': 'Example City',
            'gender': 'Other',
            'complications': 'None',
            'password': TEST_PASSWORD,
            'password_confirm': TEST_PASSWORD,
        }

        first_response = self.client.post(reverse('body:signup'), signup_data)
        duplicate_response = self.client.post(
            reverse('body:signup'),
            {
                **signup_data,
                'name': 'alex example',
                'department': 'operations',
                'position': 'coordinator',
            },
        )

        self.assertEqual(first_response.status_code, 302)
        self.assertEqual(duplicate_response.status_code, 200)
        self.assertContains(
            duplicate_response,
            'An employee with this name, department, and position is already registered.',
        )
        self.assertEqual(Body_signup.objects.count(), 1)
        self.assertEqual(Body_signup.objects.values('employee_id').distinct().count(), 1)

    def test_signup_accepts_and_displays_photo(self):
        signup_data = {
            'name': 'Jamie Sample',
            'age': 28,
            'department': 'Support',
            'position': 'Assistant',
            'residence': 'Sample City',
            'gender': 'Other',
            'complications': 'None',
            'password': TEST_PASSWORD,
            'password_confirm': TEST_PASSWORD,
        }
        photo = SimpleUploadedFile(
            'employee.png', b'test image content', content_type='image/png'
        )

        with tempfile.TemporaryDirectory() as media_root:
            with self.settings(MEDIA_ROOT=media_root):
                response = self.client.post(
                    reverse('body:signup'),
                    {
                        **signup_data,
                        'password': TEST_PASSWORD,
                        'password_confirm': TEST_PASSWORD,
                        'photo': photo,
                    },
                    follow=True,
                )

                employee = Body_signup.objects.get(name='Jamie Sample')
                self.assertTrue(employee.photo.name.startswith('employee_photos/'))
                self.assertContains(response, 'Photo of Jamie Sample')

    def test_signup_rejects_non_image_photo_extension(self):
        response = self.client.post(
            reverse('body:signup'),
            {
                'name': 'Jamie Sample',
                'age': 28,
                'department': 'Support',
                'position': 'Assistant',
                'residence': 'Sample City',
                'gender': 'Other',
                'complications': 'None',
                'password': TEST_PASSWORD,
                'password_confirm': TEST_PASSWORD,
                'photo': SimpleUploadedFile('notes.txt', b'not an image'),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Body_signup.objects.filter(name='Jamie Sample').count(), 0)

    def test_invalid_signup_does_not_create_record(self):
        response = self.client.post(reverse('body:signup'), {'name': 'Incomplete'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Body_signup.objects.count(), 0)

    def test_employee_can_log_in_with_name_position_and_password(self):
        signup_data = {
            'name': 'Morgan Employee',
            'age': 31,
            'department': 'Finance',
            'position': 'Analyst',
            'residence': 'Sample City',
            'gender': 'Other',
            'complications': 'None',
            'password': TEST_PASSWORD,
            'password_confirm': TEST_PASSWORD,
        }
        self.client.post(reverse('body:signup'), signup_data)
        employee = Body_signup.objects.get()
        session = self.client.session
        session.pop('profile_employee_id')
        session.save()

        response = self.client.post(
            reverse('body:login'),
            {
                'name': employee.name,
                'position': employee.position,
                'password': TEST_PASSWORD,
            },
            follow=True,
        )

        self.assertRedirects(response, reverse('body:index'))
        self.assertContains(response, 'Morgan Employee')
        self.assertContains(response, employee.employee_id)

    def test_login_rejects_incorrect_password(self):
        self.client.post(
            reverse('body:signup'),
            {
                'name': 'Morgan Employee',
                'age': 31,
                'department': 'Finance',
                'position': 'Analyst',
                'residence': 'Sample City',
                'gender': 'Other',
                'complications': 'None',
                'password': TEST_PASSWORD,
                'password_confirm': TEST_PASSWORD,
            },
        )
        employee = Body_signup.objects.get()
        session = self.client.session
        session.pop('profile_employee_id')
        session.save()

        response = self.client.post(
            reverse('body:login'),
            {
                'name': employee.name,
                'position': employee.position,
                'password': 'Wrong-password-456!',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Name, position, or password is incorrect.')

    def test_login_rejects_wrong_position(self):
        self.client.post(
            reverse('body:signup'),
            {
                'name': 'Morgan Employee',
                'age': 31,
                'department': 'Finance',
                'position': 'Analyst',
                'residence': 'Sample City',
                'gender': 'Other',
                'complications': 'None',
                'password': TEST_PASSWORD,
                'password_confirm': TEST_PASSWORD,
            },
        )
        session = self.client.session
        session.pop('profile_employee_id')
        session.save()

        response = self.client.post(
            reverse('body:login'),
            {
                'name': 'Morgan Employee',
                'position': 'Manager',
                'password': TEST_PASSWORD,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Name, position, or password is incorrect.')

    def test_hr_login_opens_employee_directory(self):
        hr = Body_signup.objects.create(
            name='Harper Resource',
            age=35,
            department='People',
            position='HR',
            residence='Sample City',
            gender='Other',
            complications='None',
            password_hash=make_password(TEST_PASSWORD),
            is_hr_access=True,
        )
        Body_signup.objects.create(
            name='Employee One',
            age=29,
            department='Operations',
            position='Coordinator',
            residence='Example City',
            gender='Other',
            complications='None',
            password_hash=make_password(TEST_PASSWORD),
        )

        response = self.client.post(
            reverse('body:login'),
            {
                'name': hr.name,
                'position': hr.position,
                'password': TEST_PASSWORD,
            },
        )

        self.assertRedirects(response, reverse('body:employee_directory'))
        response = self.client.get(reverse('body:employee_directory'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Employee One')
        self.assertContains(response, 'Harper Resource')
        self.assertContains(response, 'Complications')

    def test_hr_can_search_and_filter_employee_records(self):
        hr = Body_signup.objects.create(
            name='Harper Resource',
            age=35,
            department='People',
            position='HR',
            residence='Sample City',
            gender='Other',
            complications='None',
            password_hash=make_password(TEST_PASSWORD),
            is_hr_access=True,
        )
        Body_signup.objects.create(
            name='Avery Operations',
            age=29,
            department='Operations',
            position='Coordinator',
            residence='Example City',
            gender='Other',
            complications='None',
            password_hash=make_password(TEST_PASSWORD),
        )
        Body_signup.objects.create(
            name='Casey Finance',
            age=32,
            department='Finance',
            position='Analyst',
            residence='Example City',
            gender='Other',
            complications='None',
            password_hash=make_password(TEST_PASSWORD),
        )
        session = self.client.session
        session['profile_employee_id'] = hr.employee_id
        session.save()

        response = self.client.get(
            reverse('body:employee_directory'),
            {'q': 'Avery', 'department': 'Operations'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Avery Operations')
        self.assertNotContains(response, 'Casey Finance')
        self.assertEqual(response.context['result_count'], 1)

    def test_hr_can_download_employee_csv(self):
        hr = Body_signup.objects.create(
            name='Harper Resource',
            age=35,
            department='People',
            position='HR',
            residence='Sample City',
            gender='Other',
            complications='None',
            password_hash=make_password(TEST_PASSWORD),
            is_hr_access=True,
        )
        Body_signup.objects.create(
            name='Avery Operations',
            age=29,
            department='Operations',
            position='Coordinator',
            residence='Example City',
            gender='Other',
            complications='None',
            password_hash=make_password(TEST_PASSWORD),
        )
        session = self.client.session
        session['profile_employee_id'] = hr.employee_id
        session.save()

        response = self.client.get(
            reverse('body:employee_export'), {'department': 'Operations'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Type'].startswith('text/csv'))
        self.assertIn(b'Employee ID,Name,Department', response.content)
        self.assertIn(b'Avery Operations', response.content)
        self.assertNotIn(b'Harper Resource', response.content)

    def test_non_hr_employee_cannot_view_directory(self):
        employee = Body_signup.objects.create(
            name='Employee One',
            age=29,
            department='Operations',
            position='Coordinator',
            residence='Example City',
            gender='Other',
            complications='None',
            password_hash=make_password(TEST_PASSWORD),
        )
        session = self.client.session
        session['profile_employee_id'] = employee.employee_id
        session.save()

        response = self.client.get(reverse('body:employee_directory'))

        self.assertEqual(response.status_code, 403)

    def test_position_permission_grants_directory_to_employees_in_that_position(self):
        PositionPermission.objects.create(
            position='Manager',
            can_view_employee_directory=True,
        )
        first_employee = Body_signup.objects.create(
            name='Manager One',
            age=35,
            department='Operations',
            position='manager',
            residence='Sample City',
            gender='Other',
            complications='None',
            password_hash=make_password(TEST_PASSWORD),
        )
        second_employee = Body_signup.objects.create(
            name='Manager Two',
            age=36,
            department='Operations',
            position='Manager',
            residence='Sample City',
            gender='Other',
            complications='None',
            password_hash=make_password(TEST_PASSWORD),
        )

        login_response = self.client.post(
            reverse('body:login'),
            {
                'name': first_employee.name,
                'position': first_employee.position,
                'password': TEST_PASSWORD,
            },
        )
        self.assertRedirects(login_response, reverse('body:employee_directory'))

        for employee in (first_employee, second_employee):
            session = self.client.session
            session['profile_employee_id'] = employee.employee_id
            session.save()
            response = self.client.get(reverse('body:employee_directory'))
            self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('body:employee_export'))
        self.assertEqual(response.status_code, 403)

    def test_position_permission_duplicate_names_are_rejected_case_insensitive(self):
        PositionPermission.objects.create(
            position='Manager',
            can_view_employee_directory=True,
        )

        with self.assertRaisesMessage(
            ValidationError,
            'A permission rule already exists for this position.',
        ):
            PositionPermission(
                position='manager',
                can_view_employee_directory=True,
            ).save()

    def test_position_can_be_granted_csv_export_without_directory_access(self):
        PositionPermission.objects.create(
            position='Auditor',
            can_export_employee_directory=True,
        )
        employee = Body_signup.objects.create(
            name='Avery Auditor',
            age=32,
            department='Finance',
            position='Auditor',
            residence='Sample City',
            gender='Other',
            complications='None',
            password_hash=make_password(TEST_PASSWORD),
        )
        session = self.client.session
        session['profile_employee_id'] = employee.employee_id
        session.save()

        directory_response = self.client.get(reverse('body:employee_directory'))
        export_response = self.client.get(reverse('body:employee_export'))

        self.assertEqual(directory_response.status_code, 403)
        self.assertEqual(export_response.status_code, 200)
        self.assertTrue(export_response['Content-Type'].startswith('text/csv'))

    def test_non_hr_employee_cannot_export_directory(self):
        employee = Body_signup.objects.create(
            name='Employee One',
            age=29,
            department='Operations',
            position='Coordinator',
            residence='Example City',
            gender='Other',
            complications='None',
            password_hash=make_password(TEST_PASSWORD),
        )
        session = self.client.session
        session['profile_employee_id'] = employee.employee_id
        session.save()

        response = self.client.get(reverse('body:employee_export'))

        self.assertEqual(response.status_code, 403)

    def test_hr_access_cannot_be_selected_on_public_signup(self):
        signup_data = {
            'name': 'Harper Resource',
            'age': 35,
            'department': 'People',
            'position': 'HR',
            'residence': 'Sample City',
            'gender': 'Other',
            'complications': 'None',
            'password': TEST_PASSWORD,
            'password_confirm': TEST_PASSWORD,
            'is_hr_access': 'on',
        }

        self.client.post(reverse('body:signup'), signup_data)

        employee = Body_signup.objects.get(name='Harper Resource')
        self.assertFalse(employee.is_hr_access)

    def test_logout_clears_employee_profile_session(self):
        session = self.client.session
        session['profile_employee_id'] = 'EXAMPLE-EMPLOYEE-ID'
        session.save()

        response = self.client.post(reverse('body:logout'))

        self.assertRedirects(response, reverse('body:login'))
        self.assertNotIn('profile_employee_id', self.client.session)

    def test_signup_rejects_mismatched_passwords(self):
        response = self.client.post(
            reverse('body:signup'),
            {
                'name': 'Morgan Employee',
                'age': 31,
                'department': 'Finance',
                'position': 'Analyst',
                'residence': 'Sample City',
                'gender': 'Other',
                'complications': 'None',
                'password': TEST_PASSWORD,
                'password_confirm': 'Different-password-2026!',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Body_signup.objects.count(), 0)
