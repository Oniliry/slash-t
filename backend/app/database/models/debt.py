from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict

#: Статус долга: pending — ещё не погашен, confirmed — получатель подтвердил
#: перевод, netted — зачтён встречным долгом того же участника (никто никому
#: по нему уже не переводит деньги, сумма "поглощена" другим долгом).
DebtStatus = Literal["pending", "confirmed", "netted"]


class Debt(BaseModel):
    """
    Модель долга одного участника семьи (должника) перед другим (получателем),
    возникшего из конкретной покупки.
    """

    #: Уникальный идентификатор долга.
    id: int
    #: Идентификатор покупки, из которой возник долг.
    expense_id: int
    #: Идентификатор семьи, в рамках которой действует долг.
    family_id: int
    #: Идентификатор участника, который должен перевести деньги.
    debtor_id: int
    #: Идентификатор участника, которому причитается перевод (заплатил за покупку).
    creditor_id: int
    #: Сумма долга.
    amount: Decimal
    #: Текущий статус долга.
    status: DebtStatus
    #: Дата и время возникновения долга.
    created_at: datetime
    #: Дата и время подтверждения погашения, если долг уже погашен.
    confirmed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "Debt",
    "DebtStatus",
]
