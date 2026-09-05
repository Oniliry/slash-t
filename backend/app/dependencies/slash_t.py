from services.slash_t_service import SlashTService


def get_slash_t_service() -> SlashTService:
    return SlashTService()


__all__ = [
    "get_slash_t_service",
]