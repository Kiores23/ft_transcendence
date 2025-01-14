from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware

from django.middleware.csrf import get_token, rotate_token
from django.contrib.auth.models import AnonymousUser
from authenticationApp.models import CustomUser
from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.utils.decorators import sync_and_async_middleware

from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from asgiref.sync import sync_to_async

from .utils import parse_cookies, normalize_headers
from jwt import decode as jwt_decode
import hmac
import json

import logging

logger = logging.getLogger(__name__)

@database_sync_to_async
def get_user(validated_token):
    try:
        user = CustomUser.objects.get(id=validated_token["user_id"])
        return user
    except CustomUser.DoesNotExist:
        return AnonymousUser()

def compare_salted_tokens(token1, token2):
    return hmac.compare_digest(token1, token2)

class ASGIUserMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if 'user' in scope:
            # Add user to scope['headers'] so it survives ASGI to WSGI transition
            scope.setdefault('headers', []).append(
                (b'asgi-user', str(scope['user']).encode())
            )
        else:
            logger.debug(f"ASGIUserMiddleware: path={scope['path']}, user not in scope")

        return await self.inner(scope, receive, send)



@sync_and_async_middleware
class AsyncJWTAuthMiddleware:
    def __init__(self, inner):
        from authenticationApp.auth_middleware import AsyncCustomJWTAuthentication
        self.inner = inner
        self.auth = AsyncCustomJWTAuthentication()

    async def __call__(self, scope, receive, send):
        from django.utils import timezone
        from datetime import timedelta
        headers = dict(scope['headers'])
        if b'cookie' not in headers:
            scope['user'] = AnonymousUser()
            return await self.inner(scope, receive, send)

        try:
            cookies = parse_cookies(headers.get(b'cookie', b'').decode())
            request = type('MockRequest', (), {
                'COOKIES': cookies,
                'META': normalize_headers(scope['headers']),
                'method': scope.get('method', ''),
                'path': scope.get('path', '')
            })

            access_token = request.COOKIES.get('access_token')
            refresh_token = request.COOKIES.get('refresh_token')

            if access_token or refresh_token:
                try:
                    user, validated_token = await self.auth.authenticate(request)
                    scope['user'] = user
                    return await self.inner(scope, receive, send)
                except Exception as e:
                    logger.warning(f"Access token validation failed: {str(e)}")
                    # Si l'access_token est invalide/expiré, on essaie le refresh
                    if refresh_token:
                        try:
                            from rest_framework_simplejwt.tokens import RefreshToken
                            refresh = RefreshToken(refresh_token)

                            new_access_token = refresh.access_token
                            new_access_token.set_exp(from_time=timezone.now(), lifetime=timedelta(minutes=5))


                            scope['access_token'] = str(new_access_token)
                            request.COOKIES['access_token'] = scope['access_token']
                            user, validated_token = await self.auth.authenticate(request)
                            scope['user'] = user
                        except Exception as refresh_error:
                            logger.warning(f"Refresh token validation failed: {str(refresh_error)}")
                            scope['user'] = AnonymousUser()
                            scope['clear_tokens'] = True
                    else:
                        scope['user'] = AnonymousUser()
            else:
                scope['user'] = AnonymousUser()

        except Exception as e:
            logger.warning(f"Error processing request: {str(e)}")
            scope['user'] = AnonymousUser()

        return await self.inner(scope, receive, self.get_send_wrapper(send, scope))

    def get_send_wrapper(self, send, scope):
        async def send_wrapper(message):
            if message['type'] == 'http.response.start':
                headers = list(message.get('headers', []))
                if 'access_token' in scope:
                    headers.append((
                        b'set-cookie',
                        f"access_token={scope['access_token']}; HttpOnly; SameSite=Strict; Max-Age=300; Path=/".encode()
                    ))
                elif scope.get('clear_tokens'):
                    headers.extend([
                        (b'set-cookie', b'access_token=; Max-Age=0; Path=/'),
                        (b'set-cookie', b'refresh_token=; Max-Age=0; Path=/')
                    ])
                message['headers'] = headers
            await send(message)
        return send_wrapper



def AsyncJWTAuthMiddlewareStack(inner):
    return AsyncJWTAuthMiddleware(AuthMiddlewareStack(inner))

@sync_and_async_middleware
class CsrfAsgiMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def path_matches_pattern(self, path, pattern):
        path_parts = path.split('/')
        pattern_parts = pattern.split('/')
        
        if len(path_parts) != len(pattern_parts):
            return False
            
        for path_part, pattern_part in zip(path_parts, pattern_parts):
            # If pattern of the segment has {}, it is a variable
            if pattern_part.startswith('{') and pattern_part.endswith('}'):
                continue
            if path_part != pattern_part:
                return False
        return True

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.get_response(scope, receive, send)

        # Create a mock request object
        headers = dict(scope['headers'])
        cookies = parse_cookies(headers.get(b'cookie', b'').decode())
        
        normalized_headers = normalize_headers(scope['headers'])
        request = type('MockRequest', (), {
            'COOKIES': cookies,
            'META': normalized_headers,
            'method': scope.get('method', ''),
            'path': scope.get('path', '')
        })

        # Exempt routes
        exempt_patterns = [
            '/api/authentication/auth/login/',
            '/api/authentication/auth/login/2fa/',
            '/api/authentication/users/',
            '/api/authentication/users/password-reset/',
            '/api/authentication/users/password-reset-confirmation/{uid}/{token}/',
            '/api/authentication/oauth/42/callback/',
            '/api/authentication/oauth/42/authorize/',
            '/api/authentication/verify_token/',
            '/api/authentication/verify_friends/',
        ]
        logger.debug(f'request.path = {request.path}')

        # Vérifie si le chemin correspond à l'un des patterns exemptés
        for pattern in exempt_patterns:
            if self.path_matches_pattern(request.path, pattern):
                logger.debug(f'Path matches exempt pattern: {pattern}')
                return await self.get_response(scope, receive, send)

        # Check CSRF for state-changing methods
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            csrf_cookie = request.COOKIES.get('csrftoken')
            csrf_header = self.get_csrf_header(normalized_headers)

            logger.debug(f"--------------------------- CSRF_cookie = {csrf_cookie}\n")
            logger.debug(f"--------------------------- CSRF_header = {csrf_header}\n")
            if not csrf_cookie or not csrf_header:
                return await self.send_error_response(send, 'CSRF token missing', 403)

            if csrf_cookie != csrf_header:
                return await self.send_error_response(send, 'CRSF token invalid', 403)

        #async def server_send(response):
        #    await send(response)

        
        
        #return await self.get_response(scope, receive, server_send)
        return await self.get_response(scope, receive, self.get_send_wrapper(send, request))
    
    def get_send_wrapper(self, send, request):
        async def send_wrapper(message):
            if message['type'] == 'http.response.start':
                headers = list(message.get('headers', []))

                if not request.COOKIES.get('csrftoken'):
                    new_csrf_token = get_token(request)
                    csrf_cookie = (
                        f"csrftoken={new_csrf_token}; "
                        f"Path=/; "
                        f"SameSite=Strict; "
                        f"Secure=true"
                    ).encode()
                    headers.append((b'set-cookie', csrf_cookie))
                    headers.append((b'X-CSRFToken', new_csrf_token.encode()))
                
                message['headers'] = headers
            await send(message)
        return send_wrapper

    def get_csrf_header(self, headers):
        return (headers.get('HTTP_X_CSRFTOKEN') or 
                headers.get('HTTP_X_CSRF_TOKEN') or 
                headers.get('X_CSRFTOKEN') or 
                headers.get('X_CSRF_TOKEN'))

    async def send_error_response(self, send, message, status):
        await send({
            'type': 'http.response.start',
            'status': status,
            'headers': [(b'content-type', b'application/json')],
        })
        await send({
            'type': 'http.response.body',
            'body': JsonResponse({'error': message}).content,
        })

# Middleware to deactivate CSRF check of Django
class CsrfExemptMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(request, 'csrf_exempt', False):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return self.get_response(request)
