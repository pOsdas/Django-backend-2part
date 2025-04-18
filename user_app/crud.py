"""
create
read
update
delete
"""
from rest_framework import status
from django.db import IntegrityError
from typing import Sequence, Optional
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist, ValidationError


from user_app.models import User
from user_app.api.v1.serializers import CreateUser


def get_all_users() -> Sequence[User]:
    return list(User.objects.order_by("user_id"))


def get_user_by_id(
        user_id: int
) -> Optional[User]:
    try:
        user = User.objects.get(user_id=user_id)
        return user
    except ObjectDoesNotExist:
        return None


def get_user_by_username(
        username: str
) -> Optional[User]:
    try:
        user = User.objects.get(username=username)
        return user
    except ObjectDoesNotExist:
        return None


def get_user_by_email(
        email: str,
) -> Optional[User]:
    try:
        result = User.objects.filter(email=email).first()
        return result
    except ObjectDoesNotExist:
        return None


def create_user(
        *, username: str, email: str,
) -> User | Response:
    try:
        return User.objects.create(username=username, email=email)
    except IntegrityError as e:
        # пробрасываем — пусть view сам вернёт нужный HTTP-код
        raise
    except ValidationError as e:
        raise


def delete_user(
        user_id: int,
) -> Response | dict:
    user = get_user_by_id(user_id=user_id)
    if user:
        try:
            user.delete()
        except ObjectDoesNotExist:
            return Response(
                {"detail": "Failed to delete user"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    if not user:
        return Response(
            {"detail": "User not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    return {"message": "User deleted successfully", "id": id}
