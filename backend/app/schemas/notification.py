from typing import Literal, Optional

from pydantic import BaseModel, Field

NotificationKind = Literal["personal", "family", "advice"]


class NotificationItem(BaseModel):
    """Уведомление для главной страницы."""

    kind: NotificationKind = "personal"
    text: str = Field(min_length=1, max_length=500)


__all__ = [
    "NotificationItem",
    "NotificationKind",
]
