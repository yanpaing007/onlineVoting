# online_voting/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from voting.views.events import landing_page, event_list
from voting.views.auth import LoginView, RegistrationView

urlpatterns = [
    path('', landing_page, name='home'),
    path('events/', event_list, name='event_list'),
    path('admin/', admin.site.urls),
    path('voting/', include('voting.urls')),
    path('accounts/login/', LoginView.as_view(), name='login'),
    path('accounts/register/', RegistrationView.as_view(), name='register'),
    path('accounts/logout/', auth_views.LogoutView.as_view(
        http_method_names=['post', 'get'],
        next_page='home'
    ), name='logout'),
    path('accounts/password_change/', auth_views.PasswordChangeView.as_view(template_name='voting/password_change.html'), name='password_change'),
    path('accounts/password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='voting/password_change_done.html'), name='password_change_done'),
    path('accounts/password_reset/', auth_views.PasswordResetView.as_view(template_name='voting/password_reset.html'), name='password_reset'),
    path('accounts/password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='voting/password_reset_done.html'), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='voting/password_reset_confirm.html'), name='password_reset_confirm'),
    path('accounts/reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='voting/password_reset_complete.html'), name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)