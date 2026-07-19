from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from app.classroom.models import ContentBlock, utc_now
from app.classroom.session_models import (
    BaselineStepSnapshot,
    LearningSession,
    LearningSessionAccess,
    LearningSessionEvent,
    ScenePatch,
    StoredLearningSession,
)


class LearningSessionRepositoryError(ValueError):
    pass


class LearningSessionNotFoundError(LearningSessionRepositoryError):
    pass


class LearningSessionConflictError(LearningSessionRepositoryError):
    pass


class LearningSessionRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path).resolve()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def create(
        self,
        *,
        package_id: str,
        release_version: str,
        module_id: str,
        baseline_steps: list[BaselineStepSnapshot],
    ) -> LearningSessionAccess:
        if not baseline_steps:
            raise ValueError("learning session requires baseline steps")
        session_id = f"ls-{uuid4().hex[:20]}"
        access_token = secrets.token_urlsafe(32)
        now = utc_now()
        first_block_id = baseline_steps[0].blocks[0].id
        session = LearningSession(
            session_id=session_id,
            package_id=package_id,
            release_version=release_version,
            module_id=module_id,
            revision=1,
            baseline_steps=baseline_steps,
            revealed_step_ids=[baseline_steps[0].id],
            active_content_id=first_block_id,
            created_at=now,
            updated_at=now,
        )
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                INSERT INTO learning_sessions (
                    session_id, access_token_hash, snapshot_json, revision,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    self.hash_access_token(access_token),
                    self._serialize(session),
                    session.revision,
                    now,
                    now,
                ),
            )
            self._append_event(
                connection,
                session,
                "session.created",
                {"active_content_id": first_block_id},
            )
            connection.commit()
        return LearningSessionAccess(session=session, access_token=access_token)

    def get(self, session_id: str) -> StoredLearningSession:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT access_token_hash, snapshot_json
                FROM learning_sessions
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
        if row is None:
            raise LearningSessionNotFoundError(
                f"learning session not found: {session_id}"
            )
        return StoredLearningSession(
            session=LearningSession.model_validate_json(row["snapshot_json"]),
            access_token_hash=row["access_token_hash"],
        )

    def list_recent(self, *, limit: int = 20) -> list[LearningSession]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT snapshot_json
                FROM learning_sessions
                ORDER BY updated_at DESC, session_id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            LearningSession.model_validate_json(row["snapshot_json"])
            for row in rows
        ]

    def reveal(
        self,
        session_id: str,
        *,
        expected_revision: int,
    ) -> LearningSession:
        def mutate(
            connection: sqlite3.Connection,
            session: LearningSession,
        ) -> tuple[LearningSession, str, dict[str, Any]]:
            revealed = set(session.revealed_step_ids)
            next_step = next(
                (step for step in session.baseline_steps if step.id not in revealed),
                None,
            )
            if next_step is None:
                return session, "baseline.revealed", {"completed": True}
            updated = session.model_copy(
                update={
                    "revision": session.revision + 1,
                    "revealed_step_ids": [
                        *session.revealed_step_ids,
                        next_step.id,
                    ],
                    "active_content_id": next_step.blocks[0].id,
                    "updated_at": utc_now(),
                }
            )
            return updated, "baseline.revealed", {"step_id": next_step.id}

        return self._mutate(
            session_id,
            expected_revision=expected_revision,
            mutate=mutate,
        )

    def set_active_content(
        self,
        session_id: str,
        *,
        expected_revision: int,
        content_id: str,
    ) -> LearningSession:
        def mutate(
            connection: sqlite3.Connection,
            session: LearningSession,
        ) -> tuple[LearningSession, str, dict[str, Any]]:
            if content_id not in self._visible_content_ids(session):
                raise ValueError(
                    f"content target {content_id!r} is not present in the revealed scene"
                )
            if content_id == session.active_content_id:
                return session, "focus.changed", {"content_id": content_id}
            updated = session.model_copy(
                update={
                    "revision": session.revision + 1,
                    "active_content_id": content_id,
                    "updated_at": utc_now(),
                }
            )
            return updated, "focus.changed", {"content_id": content_id}

        return self._mutate(
            session_id,
            expected_revision=expected_revision,
            mutate=mutate,
        )

    def apply_patch(
        self,
        session_id: str,
        patch: ScenePatch,
        *,
        idempotency_key: str,
    ) -> LearningSession:
        request_hash = self._request_hash(patch.model_dump(mode="json"))
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            repeated = self._idempotent_result(
                connection,
                session_id,
                idempotency_key,
                request_hash,
            )
            if repeated is not None:
                connection.rollback()
                return repeated
            session = self._get_for_update(connection, session_id)
            self._require_revision(session, patch.expected_revision)
            expansion = patch.expansion
            visible_ids = self._visible_content_ids(session)
            if expansion.parent_content_id not in visible_ids:
                raise ValueError(
                    f"content target {expansion.parent_content_id!r} "
                    "is not present in the revealed scene"
                )
            expansion_ids = {item.id for item in session.expansions}
            if expansion.id in expansion_ids:
                raise LearningSessionConflictError(
                    f"expansion already exists: {expansion.id}"
                )
            if expansion.parent_expansion_id is not None:
                if (
                    not session.expansion_stack
                    or session.expansion_stack[-1] != expansion.parent_expansion_id
                ):
                    raise ValueError(
                        "nested expansion must attach to the active parent expansion"
                    )
            elif session.expansion_stack:
                raise ValueError(
                    "top-level expansion cannot replace an active nested context"
                )
            updated = session.model_copy(
                update={
                    "revision": session.revision + 1,
                    "expansions": [*session.expansions, expansion],
                    "expansion_stack": [*session.expansion_stack, expansion.id],
                    "active_content_id": expansion.blocks[0].id,
                    "updated_at": utc_now(),
                }
            )
            self._save(connection, updated)
            self._append_event(
                connection,
                updated,
                "scene.expanded",
                {
                    "expansion_id": expansion.id,
                    "parent_content_id": expansion.parent_content_id,
                    "pedagogical_intent": patch.pedagogical_intent,
                },
            )
            connection.execute(
                """
                INSERT INTO learning_session_operations (
                    session_id, idempotency_key, request_hash, response_json
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    session_id,
                    idempotency_key,
                    request_hash,
                    self._serialize(updated),
                ),
            )
            connection.commit()
            return updated

    def return_to_parent(
        self,
        session_id: str,
        *,
        expected_revision: int,
        idempotency_key: str,
    ) -> LearningSession:
        request_hash = self._request_hash(
            {"expected_revision": expected_revision, "operation": "return"}
        )
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            repeated = self._idempotent_result(
                connection,
                session_id,
                idempotency_key,
                request_hash,
            )
            if repeated is not None:
                connection.rollback()
                return repeated
            session = self._get_for_update(connection, session_id)
            self._require_revision(session, expected_revision)
            if not session.expansion_stack:
                raise ValueError("learning session has no active expansion")
            returning_id = session.expansion_stack[-1]
            returning = next(
                item for item in session.expansions if item.id == returning_id
            )
            next_stack = session.expansion_stack[:-1]
            if next_stack:
                parent = next(
                    item for item in session.expansions if item.id == next_stack[-1]
                )
                active_content_id = parent.blocks[0].id
            else:
                active_content_id = returning.parent_content_id
            updated = session.model_copy(
                update={
                    "revision": session.revision + 1,
                    "expansion_stack": next_stack,
                    "active_content_id": active_content_id,
                    "updated_at": utc_now(),
                }
            )
            self._save(connection, updated)
            self._append_event(
                connection,
                updated,
                "scene.returned",
                {"from_expansion_id": returning_id},
            )
            connection.execute(
                """
                INSERT INTO learning_session_operations (
                    session_id, idempotency_key, request_hash, response_json
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    session_id,
                    idempotency_key,
                    request_hash,
                    self._serialize(updated),
                ),
            )
            connection.commit()
            return updated

    def events_after(
        self,
        session_id: str,
        *,
        revision: int = 0,
    ) -> list[LearningSessionEvent]:
        self.get(session_id)
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT event_id, session_id, revision, kind, payload_json, created_at
                FROM learning_session_events
                WHERE session_id = ? AND revision > ?
                ORDER BY event_id
                """,
                (session_id, revision),
            ).fetchall()
        return [
            LearningSessionEvent(
                event_id=row["event_id"],
                session_id=row["session_id"],
                revision=row["revision"],
                kind=row["kind"],
                payload=json.loads(row["payload_json"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    @staticmethod
    def hash_access_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS learning_sessions (
                    session_id TEXT PRIMARY KEY,
                    access_token_hash TEXT NOT NULL,
                    snapshot_json TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS learning_session_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    kind TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(session_id) REFERENCES learning_sessions(session_id)
                );
                CREATE TABLE IF NOT EXISTS learning_session_operations (
                    session_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    request_hash TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    PRIMARY KEY(session_id, idempotency_key),
                    FOREIGN KEY(session_id) REFERENCES learning_sessions(session_id)
                );
                CREATE INDEX IF NOT EXISTS learning_session_events_lookup
                ON learning_session_events(session_id, revision, event_id);
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            timeout=30,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _mutate(
        self,
        session_id: str,
        *,
        expected_revision: int,
        mutate: Callable[
            [sqlite3.Connection, LearningSession],
            tuple[LearningSession, str, dict[str, Any]],
        ],
    ) -> LearningSession:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            session = self._get_for_update(connection, session_id)
            self._require_revision(session, expected_revision)
            updated, event_kind, event_payload = mutate(connection, session)
            if updated.revision == session.revision:
                connection.rollback()
                return session
            self._save(connection, updated)
            self._append_event(connection, updated, event_kind, event_payload)
            connection.commit()
            return updated

    def _get_for_update(
        self,
        connection: sqlite3.Connection,
        session_id: str,
    ) -> LearningSession:
        row = connection.execute(
            """
            SELECT snapshot_json
            FROM learning_sessions
            WHERE session_id = ?
            """,
            (session_id,),
        ).fetchone()
        if row is None:
            raise LearningSessionNotFoundError(
                f"learning session not found: {session_id}"
            )
        return LearningSession.model_validate_json(row["snapshot_json"])

    def _save(
        self,
        connection: sqlite3.Connection,
        session: LearningSession,
    ) -> None:
        connection.execute(
            """
            UPDATE learning_sessions
            SET snapshot_json = ?, revision = ?, updated_at = ?
            WHERE session_id = ?
            """,
            (
                self._serialize(session),
                session.revision,
                session.updated_at,
                session.session_id,
            ),
        )

    @staticmethod
    def _append_event(
        connection: sqlite3.Connection,
        session: LearningSession,
        kind: str,
        payload: dict[str, Any],
    ) -> None:
        connection.execute(
            """
            INSERT INTO learning_session_events (
                session_id, revision, kind, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                session.session_id,
                session.revision,
                kind,
                json.dumps(payload, ensure_ascii=False, sort_keys=True),
                utc_now(),
            ),
        )

    def _idempotent_result(
        self,
        connection: sqlite3.Connection,
        session_id: str,
        idempotency_key: str,
        request_hash: str,
    ) -> LearningSession | None:
        row = connection.execute(
            """
            SELECT request_hash, response_json
            FROM learning_session_operations
            WHERE session_id = ? AND idempotency_key = ?
            """,
            (session_id, idempotency_key),
        ).fetchone()
        if row is None:
            return None
        if row["request_hash"] != request_hash:
            raise LearningSessionConflictError(
                f"idempotency key {idempotency_key!r} was reused "
                "with a different request"
            )
        return LearningSession.model_validate_json(row["response_json"])

    @staticmethod
    def _require_revision(
        session: LearningSession,
        expected_revision: int,
    ) -> None:
        if session.revision != expected_revision:
            raise LearningSessionConflictError(
                f"learning session {session.session_id} is revision "
                f"{session.revision}; expected revision {expected_revision}"
            )

    @classmethod
    def _visible_content_ids(cls, session: LearningSession) -> set[str]:
        revealed = set(session.revealed_step_ids)
        target: set[str] = set()
        for step in session.baseline_steps:
            if step.id not in revealed:
                continue
            target.add(step.id)
            for block in step.blocks:
                cls._collect_block_ids(block, target)
        for expansion in session.expansions:
            target.add(expansion.id)
            for block in expansion.blocks:
                cls._collect_block_ids(block, target)
        return target

    @classmethod
    def _collect_block_ids(cls, block: ContentBlock, target: set[str]) -> None:
        target.add(block.id)
        for branch in block.detail_branches:
            target.add(branch.id)
            for child in branch.blocks:
                cls._collect_block_ids(child, target)
        if block.kind.value == "group":
            for child in block.data.get("blocks", []):
                try:
                    cls._collect_block_ids(ContentBlock.model_validate(child), target)
                except ValueError:
                    continue

    @staticmethod
    def _serialize(value: LearningSession) -> str:
        return json.dumps(
            value.model_dump(mode="json", exclude_none=True),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    @staticmethod
    def _request_hash(value: dict[str, Any]) -> str:
        payload = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
