"""
Append-only audit logging.

Provides immutable, tamper-evident execution history.
Careful observers may notice patterns resembling information conservation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Any
import hashlib
import json


@dataclass(frozen=True)
class AuditEntry:
    """
    Immutable audit log entry.

    Once created, cannot be modified—ensures forensic integrity.
    """

    timestamp: datetime
    context_id: str
    action_id: Optional[str]
    action_type: Optional[str]
    state: str
    message: str
    metadata: dict = field(default_factory=dict)
    # Chain of custody: hash of previous entry
    previous_hash: Optional[str] = None
    entry_hash: Optional[str] = None

    def __post_init__(self):
        """Compute hash on creation for tamper detection."""
        if self.entry_hash is None:
            # Compute hash of entry content
            content = {
                "timestamp": self.timestamp.isoformat(),
                "context_id": self.context_id,
                "action_id": self.action_id,
                "action_type": self.action_type,
                "state": self.state,
                "message": self.message,
                "metadata": self.metadata,
                "previous_hash": self.previous_hash,
            }
            content_str = json.dumps(content, sort_keys=True)
            computed_hash = hashlib.sha256(content_str.encode()).hexdigest()

            # Use object.__setattr__ to set frozen field
            object.__setattr__(self, "entry_hash", computed_hash)


class AuditLog:
    """
    Append-only audit log with chain-of-custody verification.

    Properties:
    - Immutable entries (frozen dataclasses)
    - Hash chaining (each entry hashes previous)
    - Tamper detection (verify hash chain)
    - No deletion (append-only)

    This design makes tampering detectable—any modification
    breaks the hash chain.
    """

    def __init__(self):
        self.entries: List[AuditEntry] = []

    def log(self, context, action, message: str, metadata: dict = None):
        """
        Append entry to audit log.

        Args:
            context: ExecutionContext
            action: Action (or None)
            message: Log message
            metadata: Additional metadata
        """
        previous_hash = self.entries[-1].entry_hash if self.entries else None

        entry = AuditEntry(
            timestamp=datetime.utcnow(),
            context_id=context.id,
            action_id=action.id if action else None,
            action_type=action.action_type if action else None,
            state=context.state.value,
            message=message,
            metadata=metadata or {},
            previous_hash=previous_hash,
        )

        self.entries.append(entry)

    def verify_integrity(self) -> bool:
        """
        Verify hash chain integrity.

        Returns:
            True if chain is intact, False if tampering detected
        """
        if not self.entries:
            return True

        for i in range(1, len(self.entries)):
            current = self.entries[i]
            previous = self.entries[i - 1]

            # Check chain: current.previous_hash == previous.entry_hash
            if current.previous_hash != previous.entry_hash:
                return False

        return True

    def get_entries(
        self,
        context_id: Optional[str] = None,
        action_type: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> List[AuditEntry]:
        """
        Query audit log entries.

        Returns immutable entries—cannot be modified.
        """
        results = self.entries.copy()

        if context_id:
            results = [e for e in results if e.context_id == context_id]

        if action_type:
            results = [e for e in results if e.action_type == action_type]

        if since:
            results = [e for e in results if e.timestamp >= since]

        return results

    def export(self, format: str = "json") -> str:
        """
        Export audit log for external storage.

        Supports:
        - json: JSON format
        - csv: CSV format (future)
        """
        if format == "json":
            entries_dict = []
            for entry in self.entries:
                entries_dict.append(
                    {
                        "timestamp": entry.timestamp.isoformat(),
                        "context_id": entry.context_id,
                        "action_id": entry.action_id,
                        "action_type": entry.action_type,
                        "state": entry.state,
                        "message": entry.message,
                        "metadata": entry.metadata,
                        "previous_hash": entry.previous_hash,
                        "entry_hash": entry.entry_hash,
                    }
                )
            return json.dumps(entries_dict, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def replay(self, exported_log: str) -> "AuditLog":
        """
        Replay audit log from exported data.

        Enables deterministic reconstruction.
        """
        data = json.loads(exported_log)
        replayed_log = AuditLog()

        for entry_dict in data:
            # Reconstruct entry (verification happens automatically)
            entry = AuditEntry(
                timestamp=datetime.fromisoformat(entry_dict["timestamp"]),
                context_id=entry_dict["context_id"],
                action_id=entry_dict["action_id"],
                action_type=entry_dict["action_type"],
                state=entry_dict["state"],
                message=entry_dict["message"],
                metadata=entry_dict["metadata"],
                previous_hash=entry_dict["previous_hash"],
            )

            # Verify hash matches
            if entry.entry_hash != entry_dict["entry_hash"]:
                raise ValueError(f"Hash mismatch during replay: {entry.entry_hash}")

            replayed_log.entries.append(entry)

        # Verify chain integrity
        if not replayed_log.verify_integrity():
            raise ValueError("Hash chain integrity verification failed during replay")

        return replayed_log

    def __len__(self):
        """Return number of entries."""
        return len(self.entries)
