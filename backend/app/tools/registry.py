from __future__ import annotations

from collections.abc import Iterable

from app.tools.contracts import ToolAdapter, ToolDefinition, ToolQualityTier


class ToolRegistryError(ValueError):
    pass


class ToolRegistryConflictError(ToolRegistryError):
    pass


class ToolNotFoundError(ToolRegistryError):
    pass


class ToolRegistry:
    def __init__(self, adapters: Iterable[ToolAdapter] = ()) -> None:
        self._adapters: dict[tuple[str, str], ToolAdapter] = {}
        for adapter in adapters:
            self.register(adapter)

    def register(self, adapter: ToolAdapter) -> None:
        definition = ToolDefinition.model_validate(adapter.definition)
        key = (definition.tool_id, definition.version)
        if key in self._adapters:
            raise ToolRegistryConflictError(
                f"tool {definition.tool_id}@{definition.version} is already registered"
            )
        self._adapters[key] = adapter

    def list(
        self,
        *,
        query: str | None = None,
        category: str | None = None,
        quality_tier: ToolQualityTier | None = None,
    ) -> list[ToolDefinition]:
        latest: dict[str, ToolAdapter] = {}
        for (tool_id, _), adapter in self._adapters.items():
            current = latest.get(tool_id)
            if current is None or self._version_key(
                adapter.definition.version
            ) > self._version_key(current.definition.version):
                latest[tool_id] = adapter

        needle = query.strip().lower() if query else None
        definitions: list[ToolDefinition] = []
        for adapter in latest.values():
            definition = adapter.definition
            if category is not None and definition.category != category:
                continue
            if quality_tier is not None and definition.quality_tier != quality_tier:
                continue
            searchable = " ".join(
                (
                    definition.tool_id,
                    definition.title,
                    definition.description,
                    definition.category,
                )
            ).lower()
            if needle and needle not in searchable:
                continue
            definitions.append(definition)
        return sorted(definitions, key=lambda item: item.tool_id)

    def get(self, tool_id: str, version: str | None = None) -> ToolAdapter:
        if version is not None:
            adapter = self._adapters.get((tool_id, version))
            if adapter is None:
                raise ToolNotFoundError(f"tool {tool_id}@{version} was not found")
            return adapter

        candidates = [
            adapter
            for (candidate_id, _), adapter in self._adapters.items()
            if candidate_id == tool_id
        ]
        if not candidates:
            raise ToolNotFoundError(f"tool {tool_id} was not found")
        return max(
            candidates,
            key=lambda adapter: self._version_key(adapter.definition.version),
        )

    @staticmethod
    def _version_key(version: str) -> tuple[int, int, int]:
        major, minor, patch = version.split(".")
        return int(major), int(minor), int(patch)
