from django.contrib import admin

from .models import Body_login, Body_signup, PositionPermission, user_info


@admin.register(Body_signup)
class BodySignupAdmin(admin.ModelAdmin):
	list_display = (
		'name',
		'employee_id',
		'phone_number',
		'department',
		'position',
		'age',
		'gender',
		'residence',
		'is_hr_access',
	)
	list_filter = ('department', 'position', 'is_hr_access')
	search_fields = ('name', 'employee_id', 'department', 'position')
	readonly_fields = ('employee_id', 'password_hash')


@admin.register(PositionPermission)
class PositionPermissionAdmin(admin.ModelAdmin):
	list_display = (
		'position',
		'can_view_employee_directory',
		'can_export_employee_directory',
	)
	list_filter = ('can_view_employee_directory', 'can_export_employee_directory')
	search_fields = ('position',)


@admin.register(Body_login)
class BodyLoginAdmin(admin.ModelAdmin):
	list_display = ('username',)
	search_fields = ('username',)


@admin.register(user_info)
class UserInfoAdmin(admin.ModelAdmin):
	list_display = ('name', 'employee_id', 'department', 'position', 'age', 'gender', 'residence')
	list_filter = ('department', 'position')
	search_fields = ('name', 'employee_id', 'department', 'position')
