from django.urls import path
from . import views

app_name = 'body'

urlpatterns = [
    path('', views.signup, name='signup'),
    path('signup/success/', views.signup_success, name='signup_success'),
    path('login/', views.employee_login, name='login'),
    path('logout/', views.employee_logout, name='logout'),
    path('homepage/', views.index, name='index'),
    path('employees/', views.employee_directory, name='employee_directory'),
    path('employees/export/', views.employee_export, name='employee_export'),
]