import httpx
from rest_framework import status
from django.db import IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema
from django.core.exceptions import ObjectDoesNotExist

from user_app.config import pydantic_settings as settings
from user_app.crud import (
    get_all_users, get_user_by_id, get_user_by_email,
    create_user, delete_user, get_user_by_username
)
from user_app.api.v1.serializers import CreateUser, ReadUserSerializer, UserSerializer, UserUpdateSerializer


# from .utils.fake_db import fake_users_db

@extend_schema(tags=["CRUD"])
class CreateUserAPIView(APIView):
    """
    Не создает записи в базе данных auth service через эту сторону.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        serializer = CreateUser(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"details": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверяем существует ли пользователь с таким email
        email = serializer.validated_data.get("email")

        if get_user_by_email(email=email):
            return Response(
                {"detail": "User with such email already exists"},
                status=status.HTTP_409_CONFLICT,
            )

        # Создаём пользователя
        try:
            user = create_user(**serializer.validated_data)
        except IntegrityError as e:
            return Response(
                {"detail": f"Integrity error: {str(e)}"},
                status=status.HTTP_409_CONFLICT,
            )
        except Exception as e:
            return Response(
                {"detail": "Internal server error: " + str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        read_serializer = ReadUserSerializer(user)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["CRUD"])
class GetUsersAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        users = get_all_users()
        if not users:
            return Response(
                {"detail": "Users not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ReadUserSerializer(instance=users, many=True)
        return Response(serializer.data)


@extend_schema(tags=["CRUD"])
class GetUserAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, user_id, *args, **kwargs):
        try:
            user = get_user_by_id(user_id=user_id)

        except ObjectDoesNotExist:
            return Response(
                {"detail": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = UserSerializer(user)
        return Response(serializer.data)


@extend_schema(tags=["CRUD"])
class GetUserByUsernameAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, username, *args, **kwargs):
        try:
            user = get_user_by_username(username=username)
        except ObjectDoesNotExist:
            return Response(
                {"detail": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UserSerializer(user)
        return Response(serializer.data)


@extend_schema(tags=["CRUD"])
class UpdateUserAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def patch(self, request, user_id, *args, **kwargs):
        serializer = UserUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {"detail": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = get_user_by_id(user_id=user_id)
        except ObjectDoesNotExist:
            return Response(
                {"detail": "User not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated = False

        if 'new_name' in serializer.validated_data:
            user.username = serializer.validated_data["new_name"]
            updated = True
        if 'email' in serializer.validated_data:
            user.email = serializer.validated_data["email"]
            updated = True
        if 'is_active' in serializer.validated_data:
            user.is_active = serializer.validated_data["is_active"]
            updated = True

        if not updated:
            return Response(
                {"detail": "No data provided for update"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user.save()
        except Exception as e:
            return Response(
                {"detail": f"Internal server error {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        serializer = UserUpdateSerializer(user)
        return Response(serializer.data)


@extend_schema(tags=["CRUD"])
class DeleteUserAPIView(APIView):
    """
    С запросом к другой стороне.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def delete(self, request, *args, **kwargs):
        user_id = kwargs.get("user_id")
        if user_id is None:
            return Response(
                {"detail": "User ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = get_user_by_id(user_id=user_id)
            # Делаем запрос к auth_app
            with httpx.Client() as client:
                response = client.delete(f"{settings.auth_service_url}/api/v1/auth/{user_id}/")

            # Пользователь не найден
            if response.status_code != 200:
                return Response(
                    {"detail": "Invalid username"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            # Пользователь найден
            try:
                delete_user(user_id=user_id)
            except Exception as e:
                return Response(
                    {"detail": f"Internal server error: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(
                {"message": "User deleted successfully", "id": user_id},
                status=status.HTTP_200_OK,
            )

        except ObjectDoesNotExist:
            return Response(
                {"detail": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )


@extend_schema(tags=["Test"])
class DeleteUserTestAPIView(APIView):
    """
    Без запроса к другой стороне.
    """
    permission_classes = [AllowAny]
    authentication_classes = []

    def delete(self, request, *args, **kwargs):
        user_id = kwargs.get("user_id")
        if user_id is None:
            return Response(
                {"detail": "User ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Пользователь найден
        try:
            delete_user(user_id=user_id)
        except Exception as e:
            return Response(
                {"detail": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"message": "User deleted successfully", "id": user_id},
            status=status.HTTP_200_OK,
        )
