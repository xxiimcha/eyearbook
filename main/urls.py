from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),  # Login view
    path('login/', views.login_view, name='login'),  # Login view
    
    path('student-login/', views.student_login_view, name='student_login'),
    
    path('profile/<int:account_id>/', views.profile_view, name='profile_page'),
    path('profile/update/', views.update_profile, name='update_profile'),
    
    path('api/get-encrypted-challenge/', views.get_encrypted_challenge, name='get_encrypted_challenge'),

    path('form/<int:account_id>/', views.form_page, name='form_page'),
    path('form/success/', views.form_page_success, name='form_page_success'),
    path('dashboard/', views.dashboard_view, name='dashboard'),  # Dashboard view
    path('configure/', views.configure, name='configure'),  # Batch management view
    path('update-batch/<int:batch_id>/', views.update_batch, name='update_batch'),  # Update batch

    # Records Module
    path('records/', views.records_view, name='records'),

    # Graduates Module
    path('batch-graduates/<int:batch_id>/', views.batch_graduates, name='batch_graduates'),  # View graduates in a batch
    path('graduates/', views.graduate_list, name='graduate_list'),  # General list of graduates
    path('graduates/<int:batch_id>/', views.graduate_list, name='batch_graduates'),  # Graduates specific to a batch
    path('graduates/add/<int:batch_id>/', views.add_graduate, name='add_graduate'),

    path('graduates/delete/<int:graduate_id>/', views.delete_graduate, name='delete_graduate'),

    path('graduates/edit/<int:pk>/', views.edit_graduate, name='edit_graduate'),  # Edit graduate

    # Accounts Module
    path('accounts/', views.account_list, name='account_list'),
    path('accounts/add-student/', views.add_student_view, name='add_student'),
    path('get_qr_code/<int:account_id>/', views.get_qr_code_data, name='view_public_key'),
    path('accounts/import/', views.import_student_view, name='import_student'),

    # Yearbook Module
    path('yearbook/', views.select_batch, name='select_batch'),
    path('yearbook/<int:from_year>/<int:to_year>/courses/', views.batch_courses, name='batch_courses'),
    path('yearbook/<int:from_year>/<int:to_year>/<str:course>/graduates/', views.course_graduates, name='course_graduates'),

    path('analytics/', views.analytics_view, name='analytics'),


    path('user-management/', views.user_management, name='user_management'),
    path('user-management/add/', views.add_user, name='add_user'),
    path('users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),

    # Logout function
    path('logout/', auth_views.LogoutView.as_view(next_page='student_login'), name='logout'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
