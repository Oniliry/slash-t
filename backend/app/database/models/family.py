from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Family(BaseModel):
    """Модель семейного пространства."""

    #: Уникальный идентификатор семьи.
    id: int
    #: Название семьи, придуманное создателем.
    name: str
    #: Код приглашения, по которому другие участники присоединяются к семье.
    invite_code: str
    #: Идентификатор пользователя, создавшего семью.
    created_by: int
    #: Дата и время создания семьи.
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "Family",
]
