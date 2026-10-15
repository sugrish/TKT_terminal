from django.contrib import admin

from .models import Body_signup


@admin.register(Body_signup)
class BodySignupAdmin(admin.ModelAdmin):
	list_display = ('name', 'employee_id', 'department', 'position', 'is_hr_access')
	list_filter = ('department', 'position', 'is_hr_access')
	search_fields = ('name', 'employee_id', 'department', 'position')
	readonly_fields = ('employee_id', 'password_hash')
