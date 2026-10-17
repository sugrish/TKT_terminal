import csv

from django.http import HttpResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
    
from .forms import BodySignupForm, EmployeeLoginForm
from .models import Body_signup, PositionPermission


def signup(request):
    form = BodySignupForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        employee = form.save()
        request.session.cycle_key()
        request.session['profile_employee_id'] = employee.employee_id
        request.session['signup_employee'] = {
            'name': employee.name,
            'department': employee.department,
            'employee_id': employee.employee_id,
            'photo_url': employee.photo.url if employee.photo else '',
        }
        return redirect('body:signup_success')

    return render(request, 'body/signup.html', {'form': form})


def signup_success(request):
    employee_details = request.session.pop('signup_employee', None)
    return render(
        request,
        'body/signup_success.html',
        {'employee': employee_details},
    )


def employee_login(request):
    form = EmployeeLoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        employee = form.authenticate()
        if employee:
            request.session.cycle_key()
            request.session['profile_employee_id'] = employee.employee_id
            if _employee_has_permission(employee, 'can_view_employee_directory'):
                return redirect('body:employee_directory')
            return redirect('body:index')
        form.add_error(None, 'Name, position, or password is incorrect.')
    return render(request, 'body/login.html', {'form': form})


@require_POST
def employee_logout(request):
    request.session.pop('profile_employee_id', None)
    return redirect('body:login')


def index(request):
    employee_id = request.session.get('profile_employee_id')
    employee = None
    if employee_id:
        employee = Body_signup.objects.filter(employee_id=employee_id).first()
    return render(
        request,
        'body/index.html',
        {
            'employee': employee,
            'can_view_employee_directory': employee is not None
            and _employee_has_permission(employee, 'can_view_employee_directory'),
        },
    )


def _employee_has_permission(employee, permission):
    if employee.is_hr_access:
        return True
    return PositionPermission.objects.filter(
        position__iexact=employee.position,
        **{permission: True},
    ).exists()


def _employee_or_permission_response(request, permission):
    employee_id = request.session.get('profile_employee_id')
    if not employee_id:
        return None, redirect('body:login')

    current_employee = Body_signup.objects.filter(employee_id=employee_id).first()
    if current_employee is None:
        request.session.pop('profile_employee_id', None)
        return None, redirect('body:login')
    if not _employee_has_permission(current_employee, permission):
        return None, HttpResponseForbidden(
            'Your position does not have permission to perform this action.'
        )
    return current_employee, None


def _filtered_employees(request):
    employees = Body_signup.objects.all()
    search_query = request.GET.get('q', '').strip()
    department = request.GET.get('department', '').strip()
    if search_query:
        employees = employees.filter(
            Q(name__icontains=search_query)
            | Q(employee_id__icontains=search_query)
            | Q(position__icontains=search_query)
        )
    if department:
        employees = employees.filter(department__iexact=department)
    return employees.order_by('name'), search_query, department


def employee_directory(request):
    current_employee, response = _employee_or_permission_response(
        request, 'can_view_employee_directory'
    )
    if response:
        return response

    employees, search_query, department = _filtered_employees(request)
    departments = Body_signup.objects.order_by('department').values_list(
        'department', flat=True
    ).distinct()
    page = Paginator(employees, 25).get_page(request.GET.get('page'))
    return render(
        request,
        'body/employee_directory.html',
        {
            'employees': page,
            'current_employee': current_employee,
            'departments': departments,
            'search_query': search_query,
            'selected_department': department,
            'result_count': employees.count(),
        },
    )


def employee_export(request):
    _, response = _employee_or_permission_response(
        request, 'can_export_employee_directory'
    )
    if response:
        return response

    employees, _, _ = _filtered_employees(request)
    csv_response = HttpResponse(content_type='text/csv; charset=utf-8')
    csv_response['Content-Disposition'] = 'attachment; filename="employees.csv"'
    writer = csv.writer(csv_response)
    writer.writerow((
        'Employee ID', 'Name', 'Department', 'Position', 'Age', 'Residence',
        'Gender', 'Photo URL', 'Complications',
    ))
    for employee in employees:
        writer.writerow((
            employee.employee_id,
            employee.name,
            employee.department,
            employee.position,
            employee.age,
            employee.residence,
            employee.gender,
            employee.photo.url if employee.photo else '',
            employee.complications,
        ))
    return csv_response