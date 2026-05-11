"""
AI 服务商业务服务
负责多服务商的选择、切换与额度管理
"""
from __future__ import annotations

from typing import Optional

from src.infrastructure.persistence.ai_provider_repository import (
    AIProvider,
    AIProviderRepository,
)


class AIProviderService:
    """多 AI 服务商管理"""

    def __init__(self, db_path: str | None = None):
        self.repo = AIProviderRepository(db_path)

    async def get_available_provider(self) -> Optional[AIProvider]:
        """按优先级返回第一个可用（启用且额度未耗尽）的服务商"""
        providers = await self.repo.find_all_enabled()
        for provider in providers:
            if not provider.is_quota_exhausted():
                return provider
        return None

    async def record_usage(self, provider_id: int) -> None:
        """记录一次 API 调用"""
        await self.repo.increment_quota_used(provider_id)

    async def switch_to_next(self, current_provider_id: int) -> Optional[AIProvider]:
        """当前服务商不可用时，切换到下一个可用服务商"""
        providers = await self.repo.find_all_enabled()
        found_current = False
        for provider in providers:
            if provider.id == current_provider_id:
                found_current = True
                continue
            if found_current and not provider.is_quota_exhausted():
                return provider
        for provider in providers:
            if provider.id == current_provider_id:
                break
            if not provider.is_quota_exhausted():
                return provider
        return None

    async def reset_provider_quota(self, provider_id: int) -> None:
        """重置指定服务商的已用额度"""
        await self.repo.reset_quota(provider_id)

    async def get_all_providers(self):
        return await self.repo.find_all()

    async def create_provider(self, data: dict) -> AIProvider:
        return await self.repo.create(data)

    async def update_provider(self, provider_id: int, data: dict):
        return await self.repo.update(provider_id, data)

    async def delete_provider(self, provider_id: int) -> bool:
        return await self.repo.delete(provider_id)
