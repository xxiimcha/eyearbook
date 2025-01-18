from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('configure/', views.configure, name='configure'),
    path('update-batch/<int:batch_id>/', views.update_batch, name='update_batch'),
]
