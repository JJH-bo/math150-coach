from __future__ import annotations

from app.classroom.model_repository import (
    ModelNotFoundError,
    TeachingModelRepository,
)
from app.classroom.models import ContentBlock
from app.classroom.repository import ClassroomNotFoundError, ClassroomRepository


class ClassroomRuntimeService:
    def __init__(
        self,
        repository: ClassroomRepository,
        *,
        model_repository: TeachingModelRepository | None = None,
    ) -> None:
        self.repository = repository
        self.model_repository = model_repository

    def catalog(self) -> dict:
        packages = [
            {
                "package_id": release.package_id,
                "title": release.package.title,
                "version": release.version,
                "content_hash": release.content_hash,
                "courses": [
                    {"id": course.id, "title": course.title}
                    for course in release.package.courses
                ],
            }
            for release in self.repository.list_active_releases()
        ]
        return {"runtime_version": "classroom_runtime_v1", "packages": packages}

    def active_package(self, package_id: str) -> dict:
        release = self.repository.get_active_release(package_id)
        return release.model_dump(mode="json", exclude_none=True)

    def module(self, package_id: str, module_id: str) -> dict:
        release = self.repository.get_active_release(package_id)
        for course in release.package.courses:
            for chapter in course.chapters:
                for module in chapter.modules:
                    if module.id == module_id:
                        content_ids = {module.id}
                        for block in module.blocks:
                            self._collect_block_ids(block, content_ids)
                        for segment in module.segments:
                            content_ids.add(segment.id)
                            for block in segment.blocks:
                                self._collect_block_ids(block, content_ids)
                        bindings = [
                            binding
                            for binding in release.package.model_bindings
                            if binding.content_id in content_ids
                        ]
                        instance_ids = {binding.instance_id for binding in bindings}
                        instances = [
                            instance
                            for instance in release.package.model_instances
                            if instance.instance_id in instance_ids
                        ]
                        return {
                            "package_id": release.package_id,
                            "version": release.version,
                            "content_hash": release.content_hash,
                            "course": {"id": course.id, "title": course.title},
                            "chapter": {"id": chapter.id, "title": chapter.title},
                            "module": module.model_dump(
                                mode="json", exclude_none=True
                            ),
                            "model_instances": [
                                instance.model_dump(mode="json", exclude_none=True)
                                for instance in instances
                            ],
                            "model_bindings": [
                                binding.model_dump(mode="json", exclude_none=True)
                                for binding in bindings
                            ],
                        }
        raise ClassroomNotFoundError(
            f"module {module_id!r} not found in package {package_id!r}"
        )

    def models(self) -> dict:
        repository = self._models()
        return {
            "models": [
                {
                    "model_id": record.model_id,
                    "version": record.version,
                    "content_hash": record.content_hash,
                    "manifest": record.manifest.model_dump(
                        mode="json",
                        exclude_none=True,
                    ),
                }
                for record in repository.list_registered()
            ]
        }

    def model(self, model_id: str, version: str) -> dict:
        record = self._models().get_registered(model_id, version)
        return {
            "model_id": record.model_id,
            "version": record.version,
            "content_hash": record.content_hash,
            "manifest": record.manifest.model_dump(mode="json", exclude_none=True),
            "source_url": (
                f"/api/classroom/v1/models/{record.model_id}"
                f"/versions/{record.version}/source.js"
            ),
        }

    def model_source(self, model_id: str, version: str) -> str:
        return self._models().get_registered(model_id, version).source

    def _models(self) -> TeachingModelRepository:
        if self.model_repository is None:
            raise ModelNotFoundError("teaching model registry is not configured")
        return self.model_repository

    @classmethod
    def _collect_block_ids(cls, block: ContentBlock, target: set[str]) -> None:
        target.add(block.id)
        for branch in block.detail_branches:
            target.add(branch.id)
            for child in branch.blocks:
                cls._collect_block_ids(child, target)
