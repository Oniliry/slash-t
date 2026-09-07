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
    BudgetSplitRequest,
    CreateFamilyRequest,
    FamilyMemberResponse,
    FamilyResponse,
    FamilyStateResponse,
    JoinFamilyRequest,
    RenameFamilyRequest,
    SetRoleRequest,
    UpdateMemberRequest,
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
    def _build_member_responses(
        members: List[User],
        created_by: int,
    ) -> List[FamilyMemberResponse]:
        """
        Считает долю каждого взрослого в общем доходе семьи, помечает админа
        и возвращает список участников в стабильном порядке по идентификатору.

        :param members: Список пользователей семьи.
        :param created_by: Идентификатор создателя (админа) семьи.
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
                    is_admin=member.id == created_by,
                )
            )

        # Порядок не должен зависеть от дохода: иначе изменение слайдера
        # меняет позиции участников и связанные с ними цвета.
        responses.sort(key=lambda item: item.id)

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
                members=self._build_member_responses(members, family.created_by),
            ),
            message="Данные семьи успешно получены.",
        )

    @staticmethod
    def _require_admin(user: User, family: Family) -> Optional[APIResponse]:
        """
        Проверяет, что текущий пользователь — админ (создатель) семьи.

        :param user: Текущий авторизованный пользователь.
        :param family: Семья, в рамках которой выполняется действие.
        :return: Ответ с ошибкой доступа, если пользователь не админ, иначе None.
        """
        if family.created_by != user.id:
            return APIResponse.fail(
                message="Изменять семью может только её создатель (админ).",
                status_code=403,
                type="admin_required",
            )
        return None

    async def _get_user_family_or_error(
        self,
        user: User,
    ) -> tuple[Optional[Family], Optional[APIResponse]]:
        """
        Достаёт семью текущего пользователя или готовый ответ с ошибкой.

        :param user: Текущий авторизованный пользователь.
        :return: Пара (семья, ошибка) — ровно одно из значений будет None.
        """
        if user.family_id is None:
            return None, APIResponse.fail(
                message="Вы ещё не состоите ни в одной семье.",
                status_code=404,
                type="family_required",
            )

        family = await self.family_repo.get_family(user.family_id)
        if family is None:
            return None, APIResponse.fail(
                message="Семья не найдена.",
                status_code=404,
                type="family_not_found",
            )

        return family, None

    async def rename_family(
        self,
        user: User,
        data: RenameFamilyRequest,
    ) -> APIResponse[FamilyResponse]:
        """
        Переименовывает семью. Доступно только админу (создателю).

        :param user: Текущий авторизованный пользователь.
        :param data: Новое название семьи.
        :return: Обновлённые данные семьи или сообщение об ошибке.
        """
        family, error = await self._get_user_family_or_error(user)
        if error is not None:
            return error

        admin_error = self._require_admin(user, family)
        if admin_error is not None:
            return admin_error

        updated_family = await self.family_repo.rename_family(family.id, data.name.strip())

        return APIResponse.success(
            data=FamilyResponse.model_validate(updated_family),
            message="Название семьи обновлено.",
        )

    async def update_member(
        self,
        user: User,
        member_id: int,
        data: UpdateMemberRequest,
    ) -> APIResponse[FamilyStateResponse]:
        """
        Обновляет имя и/или доход участника семьи. Доступно только админу.

        Доход ребёнка всегда остаётся None — присланное значение для
        участника с ролью child игнорируется.

        :param user: Текущий авторизованный пользователь (должен быть админом).
        :param member_id: Идентификатор редактируемого участника.
        :param data: Новое имя и/или доход участника.
        :return: Обновлённое состояние семьи или сообщение об ошибке.
        """
        family, error = await self._get_user_family_or_error(user)
        if error is not None:
            return error

        admin_error = self._require_admin(user, family)
        if admin_error is not None:
            return admin_error

        member = await self.user_repo.get_user(member_id)
        if member is None or member.family_id != family.id:
            return APIResponse.fail(
                message="Участник не найден в этой семье.",
                status_code=404,
                type="member_not_found",
            )

        set_income = data.monthly_income is not None and member.role == "adult"
        new_name = data.name.strip() if data.name is not None else None

        await self.user_repo.update_member_fields(
            member_id,
            name=new_name,
            monthly_income=data.monthly_income if set_income else None,
            set_income=set_income,
        )

        return await self.get_my_family(user)

    async def remove_member(
        self,
        user: User,
        member_id: int,
    ) -> APIResponse[FamilyStateResponse]:
        """
        Удаляет участника из семьи. Доступно только админу.

        Участник теряет привязку к семье, роль и доход — при следующем
        входе ему снова нужно будет создать или выбрать семью.

        :param user: Текущий авторизованный пользователь (должен быть админом).
        :param member_id: Идентификатор удаляемого участника.
        :return: Обновлённое состояние семьи или сообщение об ошибке.
        """
        family, error = await self._get_user_family_or_error(user)
        if error is not None:
            return error

        admin_error = self._require_admin(user, family)
        if admin_error is not None:
            return admin_error

        if member_id == user.id:
            return APIResponse.fail(
                message="Админ не может удалить сам себя из семьи.",
                status_code=409,
                type="cannot_remove_self",
            )

        member = await self.user_repo.get_user(member_id)
        if member is None or member.family_id != family.id:
            return APIResponse.fail(
                message="Участник не найден в этой семье.",
                status_code=404,
                type="member_not_found",
            )

        await self.user_repo.clear_user_family(member_id)

        return await self.get_my_family(user)

    async def leave_family(self, user: User) -> APIResponse[None]:
        """
        Позволяет участнику покинуть текущую семью.

        Если пользователь является создателем, права владельца автоматически
        передаются самому старому оставшемуся участнику.

        :param user: Текущий авторизованный пользователь.
        :return: Подтверждение выхода или сообщение об ошибке.
        """
        family, error = await self._get_user_family_or_error(user)
        if error is not None:
            return error

        members = await self.user_repo.get_family_members(family.id)
        if len(members) == 1:
            deleted = await self.family_repo.delete_family(family.id, user.id)
            if not deleted:
                return APIResponse.fail(
                    message="Не удалось завершить выход из семьи. Повторите попытку.",
                    status_code=409,
                    type="family_leave_conflict",
                )

            await self.user_repo.clear_user_family(user.id)
            return APIResponse.success(message="Семья удалена, вы вышли из неё.")

        left_user = await self.user_repo.leave_family(user.id, family.id)
        if left_user is None:
            return APIResponse.fail(
                message="Нельзя покинуть семью без другого участника, который примет права владельца.",
                status_code=409,
                type="last_family_member_cannot_leave",
            )

        return APIResponse.success(message="Вы покинули семью.")

    async def update_budget_split(
        self,
        user: User,
        data: BudgetSplitRequest,
    ) -> APIResponse[FamilyStateResponse]:
        """
        Перераспределяет доход между двумя соседними взрослыми участниками
        через перетаскивание точки на полоске общего бюджета.

        Сумма доходов пары остаётся неизменной, поэтому общий бюджет семьи
        не меняется — меняется только то, как он поделён внутри пары.

        :param user: Текущий авторизованный пользователь (должен быть админом).
        :param data: Пара участников и новая доля первого из них в сумме их доходов.
        :return: Обновлённое состояние семьи или сообщение об ошибке.
        """
        family, error = await self._get_user_family_or_error(user)
        if error is not None:
            return error

        admin_error = self._require_admin(user, family)
        if admin_error is not None:
            return admin_error

        if data.member_a_id == data.member_b_id:
            return APIResponse.fail(
                message="Нужны два разных участника.",
                status_code=400,
                type="invalid_member_pair",
            )

        member_a = await self.user_repo.get_user(data.member_a_id)
        member_b = await self.user_repo.get_user(data.member_b_id)

        for member in (member_a, member_b):
            if member is None or member.family_id != family.id or member.role != "adult":
                return APIResponse.fail(
                    message="Перераспределять бюджет можно только между взрослыми участниками этой семьи.",
                    status_code=404,
                    type="member_not_found",
                )

        pair_total = (member_a.monthly_income or Decimal("0")) + (member_b.monthly_income or Decimal("0"))
        ratio = Decimal(str(data.member_a_ratio))
        new_income_a = (pair_total * ratio).quantize(Decimal("0.01"))
        new_income_b = (pair_total - new_income_a).quantize(Decimal("0.01"))

        await self.user_repo.update_member_fields(
            member_a.id, name=None, monthly_income=new_income_a, set_income=True,
        )
        await self.user_repo.update_member_fields(
            member_b.id, name=None, monthly_income=new_income_b, set_income=True,
        )

        return await self.get_my_family(user)


__all__ = [
    "FamilyService",
]
