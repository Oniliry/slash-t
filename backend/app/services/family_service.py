import secrets
import string
from decimal import Decimal
from typing import List, Optional

from database.models.family import Family
from database.models.user import User, UserRole
from database.repositories.family_repo import FamilyRepository
from database.repositories.user_repo import UserRepository
from schemas.base import APIResponse
from schemas.family import (
    CreateFamilyRequest,
    FamilyMemberResponse,
    FamilyResponse,
    FamilyStateResponse,
    JoinFamilyRequest,
    SetRoleRequest,
)

#: Алфавит для генерации кода приглашения: заглавные буквы и цифры без похожих символов.
_INVITE_CODE_ALPHABET = "".join(
    sorted(set(string.ascii_uppercase + string.digits) - set("0O1I"))
)
_INVITE_CODE_LENGTH = 6


class FamilyService:
    """Сервис создания семьи, входа по коду приглашения и выбора роли участника."""

    def __init__(self, family_repo: FamilyRepository, user_repo: UserRepository):
        """
        Инициализация сервиса.

        :param family_repo: Репозиторий для работы с семьями.
        :param user_repo: Репозиторий для работы с пользователями.
        """
        self.family_repo = family_repo
        self.user_repo = user_repo

    async def _generate_invite_code(self) -> str:
        """
        Генерирует уникальный код приглашения для новой семьи.

        :return: Код приглашения, не занятый другой семьёй.
        """
        for _ in range(20):
            code = "".join(
                secrets.choice(_INVITE_CODE_ALPHABET) for _ in range(_INVITE_CODE_LENGTH)
            )
            if not await self.family_repo.invite_code_exists(code):
                return code

        raise RuntimeError("Не удалось сгенерировать уникальный код приглашения.")

    @staticmethod
    def _build_member_responses(members: List[User]) -> List[FamilyMemberResponse]:
        """
        Считает долю каждого взрослого в общем доходе семьи и собирает список участников.

        :param members: Список пользователей семьи.
        :return: Список участников с рассчитанной долей бюджета (только для взрослых).
        """
        total_income = sum(
            (member.monthly_income for member in members if member.role == "adult" and member.monthly_income),
            Decimal("0"),
        )

        responses: List[FamilyMemberResponse] = []
        for member in members:
            income_share: Optional[float] = None
            if member.role == "adult" and member.monthly_income and total_income > 0:
                income_share = float(member.monthly_income / total_income)

            responses.append(
                FamilyMemberResponse(
                    id=member.id,
                    name=member.name,
                    role=member.role,
                    monthly_income=member.monthly_income,
                    income_share=income_share,
                )
            )

        return responses

    async def create_family(
        self,
        user: User,
        data: CreateFamilyRequest,
    ) -> APIResponse[FamilyResponse]:
        """
        Создаёт новую семью и привязывает к ней текущего пользователя.

        :param user: Текущий авторизованный пользователь.
        :param data: Название новой семьи.
        :return: Данные созданной семьи с кодом приглашения или сообщение об ошибке.
        """
        if user.family_id is not None:
            return APIResponse.fail(
                message="Вы уже состоите в семье. Сначала покиньте текущую семью.",
                status_code=409,
                type="family_already_joined",
            )

        invite_code = await self._generate_invite_code()
        family = await self.family_repo.add_family(
            name=data.name,
            invite_code=invite_code,
            created_by=user.id,
        )
        await self.user_repo.set_user_family(user.id, family.id)

        return APIResponse.success(
            data=FamilyResponse.model_validate(family),
            message="Семья успешно создана.",
        )

    async def join_family(
        self,
        user: User,
        data: JoinFamilyRequest,
    ) -> APIResponse[FamilyResponse]:
        """
        Присоединяет текущего пользователя к семье по коду приглашения.

        :param user: Текущий авторизованный пользователь.
        :param data: Код приглашения семьи.
        :return: Данные семьи, к которой присоединился пользователь, или ошибку.
        """
        if user.family_id is not None:
            return APIResponse.fail(
                message="Вы уже состоите в семье. Сначала покиньте текущую семью.",
                status_code=409,
                type="family_already_joined",
            )

        normalized_code = data.invite_code.strip().upper()
        family = await self.family_repo.get_family_by_invite_code(normalized_code)
        if family is None:
            return APIResponse.fail(
                message="Семья с таким кодом приглашения не найдена.",
                status_code=404,
                type="family_not_found",
            )

        await self.user_repo.set_user_family(user.id, family.id)

        return APIResponse.success(
            data=FamilyResponse.model_validate(family),
            message="Вы успешно присоединились к семье.",
        )

    async def set_role(
        self,
        user: User,
        data: SetRoleRequest,
    ) -> APIResponse[FamilyMemberResponse]:
        """
        Сохраняет выбранную роль пользователя (взрослый/ребёнок) и его доход.

        :param user: Текущий авторизованный пользователь.
        :param data: Выбранная роль и, для взрослых, примерный месячный доход.
        :return: Данные участника семьи с ролью или сообщение об ошибке.
        """
        if user.family_id is None:
            return APIResponse.fail(
                message="Сначала создайте семью или присоединитесь к ней по коду.",
                status_code=409,
                type="family_required",
            )

        updated_user = await self.user_repo.set_user_role(
            user.id,
            role=data.role,
            monthly_income=data.monthly_income,
        )

        return APIResponse.success(
            data=FamilyMemberResponse(
                id=updated_user.id,
                name=updated_user.name,
                role=updated_user.role,
                monthly_income=updated_user.monthly_income,
                income_share=1.0 if updated_user.role == "adult" else None,
            ),
            message="Роль в семье успешно сохранена.",
        )

    async def get_my_family(self, user: User) -> APIResponse[FamilyStateResponse]:
        """
        Возвращает данные семьи текущего пользователя вместе со списком участников.

        :param user: Текущий авторизованный пользователь.
        :return: Полное состояние семьи или сообщение о том, что семьи ещё нет.
        """
        if user.family_id is None:
            return APIResponse.fail(
                message="Вы ещё не состоите ни в одной семье.",
                status_code=404,
                type="family_required",
            )

        family = await self.family_repo.get_family(user.family_id)
        if family is None:
            return APIResponse.fail(
                message="Семья не найдена.",
                status_code=404,
                type="family_not_found",
            )

        members = await self.user_repo.get_family_members(family.id)

        return APIResponse.success(
            data=FamilyStateResponse(
                family=FamilyResponse.model_validate(family),
                members=self._build_member_responses(members),
            ),
            message="Данные семьи успешно получены.",
        )


__all__ = [
    "FamilyService",
]
