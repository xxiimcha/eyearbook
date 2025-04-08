from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.landing_page, name='landing_page'),  # Login view
    path('login/', views.login_view, name='login'),  # Login view
    path('form/<int:account_id>/', views.form_page, name='form_page'),
    path('form/success/', views.form_page_success, name='form_page_success'),
    path("form/", views.form_page, name="form_page"),
    path('dashboard/', views.dashboard_view, name='dashboard'),  # Dashboard view
    path('configure/', views.configure, name='configure'),  # Batch management view
    path('update-batch/<int:batch_id>/', views.update_batch, name='update_batch'),  # Update batch

    # Graduates Module
    path('batch-graduates/<int:batch_id>/', views.batch_graduates, name='batch_graduates'),  # View graduates in a batch
    path('graduates/', views.graduate_list, name='graduate_list'),  # General list of graduates
    path('graduates/<int:batch_id>/', views.graduate_list, name='batch_graduates'),  # Graduates specific to a batch
    path('graduates/add/<int:batch_id>/', views.add_graduate, name='add_graduate'),

    path('graduates/edit/<int:pk>/', views.edit_graduate, name='edit_graduate'),  # Edit graduate
    path('graduates/delete/<int:pk>/', views.delete_graduate, name='delete_graduate'),  # Delete graduate

    # Accounts Module
    path('accounts/', views.account_list, name='account_list'),
    path('accounts/add-student/', views.add_student_view, name='add_student'),
    path('get_qr_code/<int:account_id>/', views.get_qr_code_data, name='view_public_key'),

    # Yearbook Module
    path('yearbook/', views.select_batch, name='select_batch'),
    path('yearbook/<int:from_year>/<int:to_year>/courses/', views.batch_courses, name='batch_courses'),
    path('yearbook/<int:from_year>/<int:to_year>/<str:course>/graduates/', views.course_graduates, name='course_graduates'),

    path('analytics/', views.analytics_view, name='analytics'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
