from database.models.user import User
from database.repositories.user_repo import UserRepository
from schemas.auth import UserResponse
from schemas.base import APIResponse
from schemas.profile import ChangePasswordRequest, UpdateIncomeRequest, UpdateNameRequest
from services.auth_service import AuthService


class ProfileService:
    """Сервис изменения данных профиля: имени, дохода и пароля."""

    def __init__(self, user_repo: UserRepository):
        """
        Инициализация сервиса.

        :param user_repo: Репозиторий для работы с пользователями.
        """
        self.user_repo = user_repo

    async def update_name(
        self,
        user: User,
        data: UpdateNameRequest,
    ) -> APIResponse[UserResponse]:
        """
        Меняет отображаемое имя пользователя.

        :param user: Текущий авторизованный пользователь.
        :param data: Новое имя.
        :return: Обновлённые данные пользователя.
        """
        updated_user = await self.user_repo.update_name(user.id, data.name.strip())

        return APIResponse.success(
            data=UserResponse.model_validate(updated_user),
            message="Имя успешно обновлено.",
        )

    async def update_income(
        self,
        user: User,
        data: UpdateIncomeRequest,
    ) -> APIResponse[UserResponse]:
        """
        Меняет примерный месячный доход пользователя.

        Доступно только взрослым участникам — доход ребёнка не хранится
        и не участвует в расчёте распределения трат.

        :param user: Текущий авторизованный пользователь.
        :param data: Новый месячный доход.
        :return: Обновлённые данные пользователя или сообщение об ошибке.
        """
        if user.role != "adult":
            return APIResponse.fail(
                message="Изменить доход может только участник с ролью «взрослый».",
                status_code=409,
                type="income_not_applicable",
            )

        updated_user = await self.user_repo.update_monthly_income(
            user.id,
            data.monthly_income,
        )

        return APIResponse.success(
            data=UserResponse.model_validate(updated_user),
            message="Доход успешно обновлён.",
        )

    async def change_password(
        self,
        user: User,
        data: ChangePasswordRequest,
    ) -> APIResponse[None]:
        """
        Меняет пароль пользователя после проверки текущего пароля.

        :param user: Текущий авторизованный пользователь.
        :param data: Текущий и новый пароль.
        :return: Подтверждение смены пароля или сообщение об ошибке.
        """
        current_hash = await self.user_repo.get_password_hash(user.id)
        if current_hash is None or not AuthService.verify_password(
            data.current_password,
            current_hash,
        ):
            return APIResponse.fail(
                message="Текущий пароль указан неверно.",
                status_code=401,
                type="invalid_current_password",
            )

        new_hash = AuthService.hash_password(data.new_password)
        await self.user_repo.update_password(user.id, new_hash)

        return APIResponse.success(message="Пароль успешно изменён.")


__all__ = [
    "ProfileService",
]
