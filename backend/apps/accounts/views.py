"""Account endpoints (plan Faz 7, ADR-0005: session cookie + CSRF)."""

from __future__ import annotations

import json
import logging

from django.conf import settings
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout,
    password_validation,
    update_session_auth_hash,
)
from django.contrib.auth.tokens import default_token_generator
from django.core import signing
from django.core.mail import send_mail
from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.accounts.models import Notification, SearchHistory
from apps.accounts.serializers import (
    DeleteAccountSerializer,
    LoginSerializer,
    NotificationSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    SearchHistorySerializer,
    UserSerializer,
)
from apps.accounts.services import delete_account, export_user_data

logger = logging.getLogger(__name__)
User = get_user_model()

UNSUBSCRIBE_SALT = "cineglobe.unsubscribe"


def enforce_csrf(request) -> None:
    """DRF only checks CSRF for authenticated users; sign-in/up need it too
    (otherwise a hostile site could log a visitor into the attacker's account)."""
    SessionAuthentication().enforce_csrf(request)


def _error(code: str, message: str, http_status: int, details=None) -> Response:
    return Response(
        {
            "error": {
                "code": code,
                "message": message,
                "status_code": http_status,
                "details": details,
            }
        },
        status=http_status,
    )


class AuthThrottleMixin:
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(summary="Set the CSRF cookie for the web app", tags=["Accounts"])
    def get(self, request):
        return Response({"csrfToken": get_token(request)})


class RegisterView(AuthThrottleMixin, APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Create an account and sign in",
        request=RegisterSerializer,
        responses={201: UserSerializer},
        tags=["Accounts"],
    )
    def post(self, request):
        enforce_csrf(request)
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = User.objects.create_user(
            email=data["email"],
            password=data["password"],
            preferred_language=data["preferred_language"],
            age_confirmed_at=timezone.now(),
        )
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(AuthThrottleMixin, APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Sign in with e-mail and password",
        request=LoginSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description="Invalid credentials"),
        },
        tags=["Accounts"],
    )
    def post(self, request):
        enforce_csrf(request)
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data["email"].lower(),
            password=serializer.validated_data["password"],
        )
        if user is None:
            # Same answer for unknown e-mail and wrong password (no account probing).
            return _error(
                "invalid_credentials", "E-mail or password is incorrect.", 400
            )
        login(request, user)
        return Response(UserSerializer(user).data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Sign out", request=None, responses={204: None}, tags=["Accounts"]
    )
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Current user", responses={200: UserSerializer}, tags=["Accounts"]
    )
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    @extend_schema(
        summary="Update language / e-mail notification preference",
        request=UserSerializer,
        responses={200: UserSerializer},
        tags=["Accounts"],
    )
    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(
        summary="Delete the account and all its data (password required)",
        request=DeleteAccountSerializer,
        responses={204: None},
        tags=["Accounts"],
    )
    def delete(self, request):
        serializer = DeleteAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not request.user.check_password(serializer.validated_data["password"]):
            return _error("invalid_password", "Incorrect password.", 400)
        user = request.user
        logout(request)
        delete_account(user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ExportView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(summary="Download all my data as JSON", tags=["Accounts"])
    def get(self, request):
        body = json.dumps(export_user_data(request.user), ensure_ascii=False, indent=2)
        response = HttpResponse(body, content_type="application/json; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="cineglobe-data.json"'
        return response


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Change password",
        request=PasswordChangeSerializer,
        responses={204: None},
        tags=["Accounts"],
    )
    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        update_session_auth_hash(request, request.user)  # stay signed in here only
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetRequestView(AuthThrottleMixin, APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="E-mail a password reset link (always 200)",
        request=PasswordResetRequestSerializer,
        responses={200: None},
        tags=["Accounts"],
    )
    def post(self, request):
        enforce_csrf(request)
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(
            email__iexact=serializer.validated_data["email"], is_active=True
        ).first()
        if user is not None:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            language = user.preferred_language
            link = (
                f"{settings.SITE_URL}/{language}/sifre-sifirla?uid={uid}&token={token}"
            )
            subject, body = {
                "tr": (
                    "CineGlobe şifre sıfırlama",
                    f"Şifreni sıfırlamak için: {link}\n\nBu isteği sen yapmadıysan bu e-postayı yok sayabilirsin.",
                ),
                "en": (
                    "CineGlobe password reset",
                    f"Reset your password: {link}\n\nIf you didn't ask for this, you can ignore this e-mail.",
                ),
            }[language]
            send_mail(subject, body, None, [user.email], fail_silently=True)
        # Same answer either way: the endpoint must not reveal who has an account.
        return Response(
            {"detail": "If the address has an account, a reset link was sent."}
        )


class PasswordResetConfirmView(AuthThrottleMixin, APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Set a new password with a reset link",
        request=PasswordResetConfirmSerializer,
        responses={204: None},
        tags=["Accounts"],
    )
    def post(self, request):
        enforce_csrf(request)
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(data["uid"])))
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            user = None
        if user is None or not default_token_generator.check_token(user, data["token"]):
            return _error(
                "invalid_token", "This reset link is invalid or has expired.", 400
            )
        password_validation.validate_password(data["new_password"], user)
        user.set_password(data["new_password"])
        user.save(update_fields=["password"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class SearchHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="My recent searches",
        responses={200: SearchHistorySerializer(many=True)},
        tags=["Accounts"],
    )
    def get(self, request):
        return Response(
            SearchHistorySerializer(
                SearchHistory.objects.filter(user=request.user), many=True
            ).data
        )

    @extend_schema(
        summary="Clear my search history", responses={204: None}, tags=["Accounts"]
    )
    def delete(self, request):
        SearchHistory.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SearchHistoryItemView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Delete one search", responses={204: None}, tags=["Accounts"]
    )
    def delete(self, request, pk: int):
        # 404 (not 403) for other users' rows: existence is not revealed.
        get_object_or_404(SearchHistory, pk=pk, user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="My in-app notifications",
        responses={200: NotificationSerializer(many=True)},
        tags=["Accounts"],
    )
    def get(self, request):
        items = Notification.objects.filter(user=request.user)[:50]
        unread = Notification.objects.filter(
            user=request.user, read_at__isnull=True
        ).count()
        return Response(
            {"unread": unread, "results": NotificationSerializer(items, many=True).data}
        )

    @extend_schema(
        summary="Mark all notifications read",
        request=None,
        responses={204: None},
        tags=["Accounts"],
    )
    def post(self, request):
        Notification.objects.filter(user=request.user, read_at__isnull=True).update(
            read_at=timezone.now()
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


def unsubscribe_token(user) -> str:
    return signing.dumps({"u": user.pk}, salt=UNSUBSCRIBE_SALT)


class UnsubscribeView(APIView):
    """One-click e-mail unsubscribe (KVKK/GDPR); the link works without signing in."""

    permission_classes = [AllowAny]
    authentication_classes: list = []

    @extend_schema(
        summary="Stop reminder e-mails (link from an e-mail)", tags=["Accounts"]
    )
    def get(self, request):
        try:
            payload = signing.loads(
                request.query_params.get("token", ""), salt=UNSUBSCRIBE_SALT
            )
        except signing.BadSignature:
            return _error("invalid_token", "This unsubscribe link is invalid.", 400)
        updated = User.objects.filter(pk=payload.get("u")).update(
            email_notifications=False
        )
        if not updated:
            return _error("invalid_token", "This unsubscribe link is invalid.", 400)
        return Response({"detail": "Reminder e-mails are turned off."})
