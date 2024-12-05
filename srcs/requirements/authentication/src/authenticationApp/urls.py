from django.urls import path
from .views import VerifyTokenView, UserView
from .async_views import LoginView, Setup2FAView, LogoutView, UserNicknameView, UserAvatarView, FriendsView, FriendsRequestView, NotificationsView, WebSocketTokenView, VerifyFriendsView
from .oauth_42_views import OAuth42CallbackView, OAuth42AuthorizeView

# for development
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # User management
    path('users/', UserView.as_view(), name='user_create'),
    path('users/me/', UserView.as_view(), name='user_detail'),

    # User profile management
    path('users/me/avatar/', UserAvatarView, name='user_avatar'),
    path('users/me/nickname/', UserNicknameView, name='update_nickname'),

    # Authentication
    path('auth/login/', LoginView, name='login'),
    path('auth/logout/', LogoutView, name='logout'),
    path('auth/2fa/setup/', Setup2FAView, name='Setup2FA'),

    # Friends
    path('friends/', FriendsView, name='friends'),
    path('friends/requests/', FriendsRequestView, name='friends_requests'),

    # Notifications
    path('notifications/', NotificationsView, name='notifications'),

    # For backends
    path('verify_token/', VerifyTokenView.as_view(), name='verify_token'),
    path('verify_friends/', VerifyFriendsView, name='verify_friends'),

    #path('auth/token/get-access/', WebSocketTokenView.as_view(), name='get_websocket_token'),
    path('auth/token/get-access/', WebSocketTokenView, name='get_websocket_token'),

    # OAUTH 42 API
    path('oauth/42/callback/', OAuth42CallbackView, name='oauth_42_callback'),
    path('oauth/42/authorize/', OAuth42AuthorizeView, name='oauth_42_authorize'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

'''

    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),


    '''


