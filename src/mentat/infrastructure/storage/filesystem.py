"""Filesystem storage backend implementation."""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .interfaces import BaseStorageBackend


class FilesystemStorageBackend(BaseStorageBackend):
    """File system-based storage backend."""

    def __init__(self, base_path: Optional[Path] = None):
        """Initialize filesystem storage backend."""
        super().__init__(base_path)
        self.sessions_dir = self.base_path / "sessions"
        self.conversations_dir = self.base_path / "conversations"
        self.context_dir = self.base_path / "context"

        # Create directories if they don't exist
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
        self.context_dir.mkdir(parents=True, exist_ok=True)

    def _session_file_path(self, session_id: str) -> Path:
        """Get file path for session data."""
        return self.sessions_dir / f"{session_id}.json"

    def _conversation_file_path(self, session_id: str, conversation_id: str) -> Path:
        """Get file path for conversation data."""
        session_conv_dir = self.conversations_dir / session_id
        session_conv_dir.mkdir(exist_ok=True)
        return session_conv_dir / f"{conversation_id}.json"

    def _context_file_path(self, project_path: str) -> Path:
        """Get file path for project context data."""
        # Convert project path to safe filename
        resolved_path = str(Path(project_path).resolve())
        safe_name = resolved_path.replace(":", "").replace("\\", "_").replace("/", "_")
        return self.context_dir / f"{safe_name}.json"

    async def store_session(self, session_id: str, data: Dict[str, Any]) -> None:
        """Store session data to filesystem."""
        file_path = self._session_file_path(session_id)

        # Add timestamp
        data_with_timestamp = {
            **data,
            "stored_at": datetime.now().isoformat(),
            "session_id": session_id,
        }

        def _write_file() -> None:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data_with_timestamp, f, indent=2, default=str)

        await asyncio.get_event_loop().run_in_executor(None, _write_file)

    async def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session data from filesystem."""
        file_path = self._session_file_path(session_id)

        if not file_path.exists():
            return None

        def _read_file() -> Optional[Dict[str, Any]]:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None

        return await asyncio.get_event_loop().run_in_executor(None, _read_file)

    async def list_sessions(self) -> List[str]:
        """List all session IDs."""

        def _list_files() -> List[str]:
            session_files = []
            for file_path in self.sessions_dir.glob("*.json"):
                session_files.append(file_path.stem)
            return session_files

        return await asyncio.get_event_loop().run_in_executor(None, _list_files)

    async def delete_session(self, session_id: str) -> bool:
        """Delete session data from filesystem."""
        file_path = self._session_file_path(session_id)

        def _delete_file() -> bool:
            try:
                if file_path.exists():
                    file_path.unlink()
                    # Also delete associated conversations
                    session_conv_dir = self.conversations_dir / session_id
                    if session_conv_dir.exists():
                        for conv_file in session_conv_dir.glob("*.json"):
                            conv_file.unlink()
                        session_conv_dir.rmdir()
                    return True
                return False
            except OSError:
                return False

        return await asyncio.get_event_loop().run_in_executor(None, _delete_file)

    async def store_conversation(
        self, session_id: str, conversation_id: str, messages: List[Dict[str, Any]]
    ) -> None:
        """Store conversation messages to filesystem."""
        file_path = self._conversation_file_path(session_id, conversation_id)

        conversation_data = {
            "session_id": session_id,
            "conversation_id": conversation_id,
            "messages": messages,
            "stored_at": datetime.now().isoformat(),
            "message_count": len(messages),
        }

        def _write_file() -> None:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(conversation_data, f, indent=2, default=str)

        await asyncio.get_event_loop().run_in_executor(None, _write_file)

    async def load_conversation(
        self, session_id: str, conversation_id: str
    ) -> List[Dict[str, Any]]:
        """Load conversation messages from filesystem."""
        file_path = self._conversation_file_path(session_id, conversation_id)

        if not file_path.exists():
            return []

        def _read_file() -> List[Dict[str, Any]]:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("messages", [])
            except (json.JSONDecodeError, IOError):
                return []

        return await asyncio.get_event_loop().run_in_executor(None, _read_file)

    async def store_project_context(self, project_path: str, context: Dict[str, Any]) -> None:
        """Store project context data to filesystem."""
        file_path = self._context_file_path(project_path)

        context_data = {
            **context,
            "project_path": project_path,
            "stored_at": datetime.now().isoformat(),
        }

        def _write_file() -> None:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(context_data, f, indent=2, default=str)

        await asyncio.get_event_loop().run_in_executor(None, _write_file)

    async def load_project_context(self, project_path: str) -> Optional[Dict[str, Any]]:
        """Load project context data from filesystem."""
        file_path = self._context_file_path(project_path)

        if not file_path.exists():
            return None

        def _read_file() -> Optional[Dict[str, Any]]:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None

        return await asyncio.get_event_loop().run_in_executor(None, _read_file)

    async def cleanup_old_sessions(self, max_age_days: int = 30) -> int:
        """Clean up old sessions from filesystem."""
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        deleted_count = 0

        def _cleanup() -> None:
            nonlocal deleted_count
            for file_path in self.sessions_dir.glob("*.json"):
                try:
                    # Check file modification time
                    mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mod_time < cutoff_date:
                        session_id = file_path.stem
                        # Delete session file
                        file_path.unlink()

                        # Delete associated conversations
                        session_conv_dir = self.conversations_dir / session_id
                        if session_conv_dir.exists():
                            for conv_file in session_conv_dir.glob("*.json"):
                                conv_file.unlink()
                            session_conv_dir.rmdir()

                        deleted_count += 1
                except (OSError, ValueError):
                    # Skip files that can't be processed
                    continue

        await asyncio.get_event_loop().run_in_executor(None, _cleanup)
        return deleted_count
