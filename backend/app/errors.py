from __future__ import annotations

from fastapi import HTTPException


class AppError(HTTPException):
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(
            status_code=status_code,
            detail={"error": {"code": code, "message": message}},
        )


class NotFoundError(AppError):
    def __init__(self, entity: str, id: int | str):
        super().__init__(404, "NOT_FOUND", f"{entity} {id} not found")


class ValidationError(AppError):
    def __init__(self, message: str):
        super().__init__(422, "VALIDATION_ERROR", message)


class ProviderNotConfiguredError(AppError):
    def __init__(self, capability: str, provider: str):
        super().__init__(
            503,
            "PROVIDER_NOT_CONFIGURED",
            f"{capability} provider '{provider}' is not configured. Check your .env file.",
        )


class ProviderAPIError(AppError):
    def __init__(self, capability: str, message: str):
        super().__init__(503, "PROVIDER_API_ERROR", f"{capability}: {message}")


class AudioMissingError(AppError):
    def __init__(self, item_id: int):
        super().__init__(404, "AUDIO_MISSING", f"Audio file for item {item_id} not found")
