"""Account serializers (plan Faz 7)."""

from __future__ import annotations

from django.contrib.auth import get_user_model, password_validation
from rest_framework import serializers

from apps.accounts.models import Notification, SearchHistory

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "preferred_language",
            "email_notifications",
            "date_joined",
        ]
        read_only_fields = ["id", "email", "date_joined"]


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    preferred_language = serializers.ChoiceField(choices=["tr", "en"], default="tr")
    # Plan v1.7: accounts are 18+ by self-declaration; no birth date is collected.
    age_confirmed = serializers.BooleanField()

    def validate_email(self, value: str) -> str:
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "An account with this e-mail already exists."
            )
        return value

    def validate_age_confirmed(self, value: bool) -> bool:
        if not value:
            raise serializers.ValidationError("You must confirm you are 18 or older.")
        return value

    def validate(self, attrs):
        password_validation.validate_password(
            attrs["password"], User(email=attrs["email"])
        )
        return attrs


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError(
                {"current_password": "Incorrect password."}
            )
        password_validation.validate_password(attrs["new_password"], user)
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)


class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = ["id", "query", "media_type", "language", "created_at"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "kind",
            "message",
            "media_type",
            "tmdb_id",
            "created_at",
            "read_at",
        ]
