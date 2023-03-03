from allauth.account.views import ConfirmEmailView
from allauth.account.models import EmailConfirmationHMAC
from rest_framework.exceptions import ValidationError
from rest_framework.generics import CreateAPIView, RetrieveUpdateAPIView, GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from core.serializers import EmptySerializer
from .serializers import (
    UserProfileSerializer,
    DeleteUserSerializer,
    DisableUserSerializer,
)


class VerifyUserView(CreateAPIView, ConfirmEmailView):
    serializer_class = EmptySerializer

    def perform_create(self, serializer):
        confirmation = self.get_object()
        confirmation.confirm(self.request)
        return confirmation

    def get_queryset(self):
        return super().get_queryset()

    def get_object(self, queryset=None):
        key = self.kwargs["key"]
        confirmation = EmailConfirmationHMAC.from_key(key)
        if not confirmation:
            raise ValidationError("Invalid confirmation key")
        return confirmation


class UserProfileView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user


class DisableUserProfileView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DisableUserSerializer

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        is_disabled = serializer.validated_data.get("is_disabled", False)
        user.is_disabled = is_disabled
        user.save()
        response_data = {"message": f"{user.email} is  disabled ({is_disabled})"}
        return Response(status=status.HTTP_200_OK, data=response_data)


class DeleteUserProfileView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DeleteUserSerializer

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        is_deleted = serializer.validated_data.get("is_deleted", False)
        reason_to_delete = serializer.validated_data.get("reason_to_delete", False)
        password = serializer.validated_data.get("password", False)
        correct_password = user.check_password(password)
        if not correct_password:
            return Response(
                status=status.HTTP_401_UNAUTHORIZED,
                data={"message": "password is incorrect"},
            )
        response_data = {"is_deleted": is_deleted}
        if is_deleted:
            user.is_active = False
            user.reason_to_delete = reason_to_delete
            user.save()
            response_data = {"message": f"{user.email} is deleted ({is_deleted})"}
            user.delete()
        return Response(status=status.HTTP_200_OK, data=response_data)
