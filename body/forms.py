from pathlib import Path

from django import forms
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import validate_password

from .models import Body_signup

GENDER_CHOICES = [
    ('Male', 'Male'),
    ('Female', 'Female'),
]

DEPARTMENT_CHOICES = [
    ('Admin', 'Admin'),
    ('Maintenance', 'Maintenance'),
    ('Facility', 'Facility'),
]

POSITION_CHOICES = [
    ('Employee', 'Employee'),
    ('CEO', 'CEO'),
    ('COO', 'COO'),
    ('HR', 'HR'),
    ('Manager', 'Manager'),
    ('Fin Sec', 'Fin Sec'),
    ('Other', 'Other'),
]


class BodySignupForm(forms.ModelForm):
    gender = forms.CharField(
        label='Sex',
        widget=forms.Select(choices=GENDER_CHOICES),
    )
    department = forms.CharField(
        widget=forms.Select(choices=DEPARTMENT_CHOICES),
    )
    position = forms.CharField(
        widget=forms.Select(choices=POSITION_CHOICES),
    )
    password = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput,
        validators=[validate_password],
    )
    password_confirm = forms.CharField(
        label='Confirm password',
        strip=False,
        widget=forms.PasswordInput,
    )

    class Meta:
        model = Body_signup
        fields = (
            'name',
            'age',
            'department',
            'position',
            'residence',
            'gender',
            'complications',
            'photo',
        )
        widgets = {
            'photo': forms.ClearableFileInput(
                attrs={'accept': '.jpg,.jpeg,.png,.webp'}
            ),
        }

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo:
            extension = Path(photo.name).suffix.lower()
            if extension not in {'.jpg', '.jpeg', '.png', '.webp'}:
                raise forms.ValidationError('Upload a JPG, PNG, or WEBP image.')
            if photo.size > 5 * 1024 * 1024:
                raise forms.ValidationError('The photo must be 5 MB or smaller.')
        return photo

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'The passwords do not match.')

        name = cleaned_data.get('name', '').strip()
        department = cleaned_data.get('department', '').strip()
        position = cleaned_data.get('position', '').strip()
        if name and department and position:
            existing = Body_signup.objects.filter(
                name__iexact=name,
                department__iexact=department,
                position__iexact=position,
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise forms.ValidationError(
                    'An employee with this name, department, and position '
                    'is already registered.'
                )
        return cleaned_data

    def save(self, commit=True):
        employee = super().save(commit=False)
        employee.password_hash = make_password(self.cleaned_data['password'])
        if commit:
            employee.save()
            self.save_m2m()
        return employee


class EmployeeLoginForm(forms.Form):
    name = forms.CharField(max_length=100, label='Full name')
    position = forms.CharField(
        label='Position',
        widget=forms.Select(choices=POSITION_CHOICES),
    )
    password = forms.CharField(strip=False, widget=forms.PasswordInput)

    def authenticate(self):
        name = self.cleaned_data['name'].strip()
        position = self.cleaned_data['position'].strip()
        password = self.cleaned_data['password']
        matches = [
            employee
            for employee in Body_signup.objects.filter(
                name__iexact=name,
                position__iexact=position,
            )
            if employee.password_hash
            and check_password(password, employee.password_hash)
        ]
        return matches[0] if len(matches) == 1 else None
