"""
ZenConnection - Thread-safe connection manager for Actian Zen database.

Features:
- Thread-local ODBC connections (one per thread, no sharing)
- Shared SQLAlchemy engine with QueuePool (thread-safe by design)
- Per-instance transaction state with locking
- Connection validation and auto-reconnect
- Clean shutdown with resource cleanup

Based on design from: docs/thread-safety.md
"""

import threading
import time
from typing import Optional
import pyodbc
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool


class ZenConnection:
    """
    Thread-safe connection manager for Zen database.

    - Raw ODBC: Thread-local connections (one per thread)
    - SQLAlchemy: Shared engine with QueuePool (thread-safe by design)
    - Transaction state: Per-instance (per MCP session)
    """

    TRANSACTION_TIMEOUT = 300  # 5 minutes

    def __init__(
        self,
        conn_string: str,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_recycle: int = 3600
    ):
        """
        Initialize connection manager.

        Args:
            conn_string: ODBC connection string (DSN= or DRIVER= format)
            pool_size: SQLAlchemy pool size (default 5)
            max_overflow: Extra connections under load (default 10)
            pool_recycle: Recycle connections after N seconds (default 3600)
        """
        self.conn_string = conn_string
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_recycle = pool_recycle

        # Thread-local storage for raw ODBC connections
        self._odbc_local = threading.local()

        # Shared SQLAlchemy engine (QueuePool is thread-safe)
        self._engine = None
        self._engine_lock = threading.Lock()

        # Per-instance transaction state
        self._transaction_active = False
        self._transaction_connection = None
        self._transaction_start = None
        self._transaction_lock = threading.Lock()

    # ─────────────────────────────────────────────────────────────────────────
    # Raw ODBC Connection (Thread-Local)
    # ─────────────────────────────────────────────────────────────────────────

    def get_odbc_connection(self) -> pyodbc.Connection:
        """
        Get thread-local ODBC connection.

        Each thread gets its own connection — no sharing, no race conditions.
        If transaction is active, returns the transaction connection instead.

        Returns:
            pyodbc.Connection for current thread
        """
        # If transaction is active, return transaction connection
        if self._transaction_active and self._transaction_connection:
            return self._transaction_connection

        # Check thread-local connection
        if not hasattr(self._odbc_local, 'connection'):
            self._odbc_local.connection = None

        needs_new = False

        if self._odbc_local.connection is None:
            needs_new = True
        else:
            # Validate existing connection
            try:
                cursor = self._odbc_local.connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
            except Exception:
                # Connection is dead, recreate
                needs_new = True
                try:
                    self._odbc_local.connection.close()
                except Exception:
                    pass
                self._odbc_local.connection = None

        if needs_new:
            self._odbc_local.connection = pyodbc.connect(
                self.conn_string,
                autocommit=False
            )

        return self._odbc_local.connection

    def close_odbc_connection(self):
        """Close thread-local ODBC connection."""
        if hasattr(self._odbc_local, 'connection') and self._odbc_local.connection:
            try:
                self._odbc_local.connection.close()
            except Exception:
                pass
            self._odbc_local.connection = None

    # ─────────────────────────────────────────────────────────────────────────
    # SQLAlchemy Engine (Shared, Thread-Safe via QueuePool)
    # ─────────────────────────────────────────────────────────────────────────

    def get_engine(self):
        """
        Get shared SQLAlchemy engine.

        QueuePool manages connections and is thread-safe by design.
        Uses double-checked locking for thread-safe initialization.
        """
        if self._engine is None:
            with self._engine_lock:
                if self._engine is None:  # Double-check after acquiring lock
                    self._engine = create_engine(
                        f"zen://?odbc_connect={self.conn_string}",
                        echo=False,
                        poolclass=QueuePool,
                        pool_size=self.pool_size,
                        max_overflow=self.max_overflow,
                        pool_pre_ping=True,  # Test connections before use
                        pool_recycle=self.pool_recycle
                    )
        return self._engine

    def dispose_engine(self):
        """Dispose SQLAlchemy engine and all pooled connections."""
        if self._engine:
            with self._engine_lock:
                if self._engine:
                    self._engine.dispose()
                    self._engine = None

    # ─────────────────────────────────────────────────────────────────────────
    # Transaction Management (Per-Instance, Thread-Safe)
    # ─────────────────────────────────────────────────────────────────────────

    def begin_transaction(self) -> dict:
        """
        Start transaction and return dedicated connection.

        Returns:
            dict with success status and message
        """
        with self._transaction_lock:
            # Check for orphaned transaction (timeout)
            self._check_transaction_timeout()

            if self._transaction_active:
                return {
                    "error": "Transaction already active for this session",
                    "success": False
                }

            self._transaction_connection = pyodbc.connect(
                self.conn_string,
                autocommit=False
            )
            self._transaction_active = True
            self._transaction_start = time.time()

            return {
                "success": True,
                "message": "Transaction started. Use commit_transaction() or rollback_transaction() when done."
            }

    def get_transaction_connection(self) -> Optional[pyodbc.Connection]:
        """Get connection for active transaction (or None)."""
        return self._transaction_connection if self._transaction_active else None

    def is_transaction_active(self) -> bool:
        """Check if transaction is active for this session."""
        return self._transaction_active

    def commit_transaction(self) -> dict:
        """Commit and close transaction connection."""
        with self._transaction_lock:
            if not self._transaction_active:
                return {
                    "error": "No active transaction",
                    "success": False
                }

            try:
                self._transaction_connection.commit()
                return {
                    "success": True,
                    "message": "Transaction committed successfully"
                }
            finally:
                self._cleanup_transaction()

    def rollback_transaction(self) -> dict:
        """Rollback and close transaction connection."""
        with self._transaction_lock:
            if not self._transaction_active:
                return {
                    "error": "No active transaction",
                    "success": False
                }

            try:
                self._transaction_connection.rollback()
                return {
                    "success": True,
                    "message": "Transaction rolled back successfully"
                }
            finally:
                self._cleanup_transaction()

    def _cleanup_transaction(self):
        """Clean up transaction state."""
        if self._transaction_connection:
            try:
                self._transaction_connection.close()
            except Exception:
                pass
        self._transaction_active = False
        self._transaction_connection = None
        self._transaction_start = None

    def _check_transaction_timeout(self):
        """Auto-rollback if transaction exceeded timeout."""
        if self._transaction_active and self._transaction_start:
            elapsed = time.time() - self._transaction_start
            if elapsed > self.TRANSACTION_TIMEOUT:
                # Force rollback of stale transaction
                try:
                    self._transaction_connection.rollback()
                except Exception:
                    pass
                self._cleanup_transaction()
                raise TimeoutError(
                    f"Previous transaction timed out after {elapsed:.0f}s and was rolled back"
                )

    # ─────────────────────────────────────────────────────────────────────────
    # Cleanup (All Resources)
    # ─────────────────────────────────────────────────────────────────────────

    def release_all_locks(self) -> dict:
        """
        Release ALL connections and locks.

        Use for DDL Error 85 recovery or before table modifications.

        Returns:
            dict with list of closed resources
        """
        closed = []

        # Close thread-local ODBC
        if hasattr(self._odbc_local, 'connection') and self._odbc_local.connection:
            try:
                self._odbc_local.connection.close()
                closed.append("Thread-local ODBC connection")
            except Exception:
                pass
            self._odbc_local.connection = None

        # Rollback and close any active transaction
        if self._transaction_active:
            try:
                self._transaction_connection.rollback()
                self._transaction_connection.close()
                closed.append("Transaction connection (rolled back)")
            except Exception:
                pass
            self._transaction_active = False
            self._transaction_connection = None
            self._transaction_start = None

        # Dispose SQLAlchemy engine
        if self._engine:
            try:
                self._engine.dispose()
                closed.append("SQLAlchemy engine (disposed)")
            except Exception:
                pass
            self._engine = None

        return {
            "success": True,
            "closed": closed,
            "message": f"Released {len(closed)} resource(s)"
        }

    async def cleanup(self):
        """
        Called on server shutdown.

        Releases all resources gracefully.
        """
        self.release_all_locks()

    def __repr__(self):
        # only show DSN name or driver, never uid/pwd
        s = self.conn_string
        for key in ("DSN=", "DRIVER="):
            if key in s.upper():
                start = s.upper().index(key)
                end = s.index(";", start) if ";" in s[start:] else len(s)
                return f"ZenConnection({s[start:end]})"
        return "ZenConnection(***)"
