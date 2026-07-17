from __future__ import annotations

from app.classroom.repository import ClassroomNotFoundError, ClassroomRepository


class ClassroomRuntimeService:
    def __init__(self, repository: ClassroomRepository) -> None:
        self.repository = repository

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
                        return {
                            "package_id": release.package_id,
                            "version": release.version,
                            "content_hash": release.content_hash,
                            "course": {"id": course.id, "title": course.title},
                            "chapter": {"id": chapter.id, "title": chapter.title},
                            "module": module.model_dump(
                                mode="json", exclude_none=True
                            ),
                        }
        raise ClassroomNotFoundError(
            f"module {module_id!r} not found in package {package_id!r}"
        )
