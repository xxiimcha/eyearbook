from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.login_view, name='login'),  # Login view
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
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
