import re

from django.db import models
from django.utils import timezone


def _employee_id_segment(value):
    segment = re.sub(r'[^A-Za-z0-9]+', '-', value).strip('-').upper()
    return segment or 'UNKNOWN'


class Body_signup(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    department = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    residence = models.CharField(max_length=100)
    gender = models.CharField(max_length=10)
    complications = models.TextField()
    employee_id = models.CharField(max_length=200, unique=True, editable=False)
    photo = models.FileField(upload_to='employee_photos/', blank=True)
    password_hash = models.CharField(max_length=128, blank=True)
    is_hr_access = models.BooleanField(
        default=False,
        help_text='Allow this employee to view the employee directory.',
    )

    def save(self, *args, **kwargs):
        if not self.employee_id:
            name_parts = self.name.split()
            initials = ''.join(part[0] for part in name_parts[:2]).upper() or 'X'
            base_id = '-'.join(
                (
                    _employee_id_segment(self.position),
                    _employee_id_segment(self.department),
                    initials,
                    str(timezone.localdate().year),
                )
            )

            self.employee_id = base_id
            suffix = 2
            while Body_signup.objects.filter(employee_id=self.employee_id).exclude(pk=self.pk).exists():
                self.employee_id = f'{base_id}-{suffix}'
                suffix += 1

        super().save(*args, **kwargs)

class Body_login(models.Model):
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    #the password will be similar for employess and different for admin. The admin password will be hardcoded in the code and will be used to access the admin panel. The employee password will be stored in the database and will be used to access the employee panel.
# Create your models here.


class user_info(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    department = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    residence = models.CharField(max_length=100)
    gender = models.CharField(max_length=10)
    complications = models.TextField()
    employee_id = models.CharField(max_length=100, unique=True)
