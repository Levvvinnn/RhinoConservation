import sqlite3
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

DB_PATH = Path(__file__).parent / "rhino_conservation.db"


def get_db_conn():
    """Get a database connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def db_conn():
    """Context manager for a database connection (auto-commit/rollback)."""
    conn = get_db_conn()
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize database with all required tables."""
    with db_conn() as conn:
        c = conn.cursor()

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                phone TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS rhinos (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                species TEXT NOT NULL,
                collar_id TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'active',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                health_notes TEXT
            )
        """
        )

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rhino_id TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                altitude REAL,
                accuracy REAL,
                sats INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(rhino_id) REFERENCES rhinos(id)
            )
        """
        )

        c.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rhino_id TEXT NOT NULL,
                alert_type TEXT,
                message TEXT,
                resolved INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(rhino_id) REFERENCES rhinos(id)
            )
        """
        )

        c.execute("CREATE INDEX IF NOT EXISTS idx_locations_rhino_id ON locations(rhino_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_locations_timestamp ON locations(timestamp)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_alerts_rhino_id ON alerts(rhino_id)")



def create_rhino(rhino_id: str, name: str, species: str, collar_id: str, status: str = "active") -> bool:
    """Create a new rhino record."""
    try:
        with db_conn() as conn:
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO rhinos (id, name, species, collar_id, status)
                VALUES (?, ?, ?, ?, ?)
            """,
                (rhino_id, name, species, collar_id, status),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def get_rhino(rhino_id: str) -> Optional[Dict]:
    """Get a single rhino by ID."""
    with db_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM rhinos WHERE id = ?", (rhino_id,))
        row = c.fetchone()
    return dict(row) if row else None


def get_all_rhinos() -> List[Dict]:
    """Get all rhinos."""
    with db_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM rhinos ORDER BY created_at DESC")
        rows = c.fetchall()
    return [dict(row) for row in rows]


def update_rhino(rhino_id: str, name: str = None, status: str = None, health_notes: str = None) -> bool:
    """Update rhino information."""
    updates = []
    params = []
    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if status is not None:
        updates.append("status = ?")
        params.append(status)
    if health_notes is not None:
        updates.append("health_notes = ?")
        params.append(health_notes)

    if not updates:
        return False

    params.append(rhino_id)
    query = f"UPDATE rhinos SET {', '.join(updates)} WHERE id = ?"

    try:
        with db_conn() as conn:
            c = conn.cursor()
            c.execute(query, params)
            return c.rowcount > 0
    except Exception:
        return False


def delete_rhino(rhino_id: str) -> bool:
    """Delete a rhino record (soft delete via status)."""
    return update_rhino(rhino_id, status="inactive")




def add_location(rhino_id: str, latitude: float, longitude: float, altitude: float = None, accuracy: float = None, sats: int = None) -> bool:
    """Add a new GPS location for a rhino."""
    try:
        with db_conn() as conn:
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO locations (rhino_id, latitude, longitude, altitude, accuracy, sats)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (rhino_id, latitude, longitude, altitude, accuracy, sats),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def get_location_history(rhino_id: str, limit: int = 100) -> List[Dict]:
    """Get location history for a rhino."""
    with db_conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT * FROM locations
            WHERE rhino_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (rhino_id, limit),
        )
        rows = c.fetchall()
    return [dict(row) for row in rows]


def get_latest_location(rhino_id: str) -> Optional[Dict]:
    """Get the most recent location for a rhino."""
    with db_conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT * FROM locations
            WHERE rhino_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """,
            (rhino_id,),
        )
        row = c.fetchone()
    return dict(row) if row else None


def get_all_latest_locations() -> List[Dict]:
    """Get the latest location for each rhino."""
    with db_conn() as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT l.* FROM locations l
            WHERE l.timestamp = (
                SELECT MAX(timestamp) FROM locations WHERE rhino_id = l.rhino_id
            )
            ORDER BY l.rhino_id
        """
        )
        rows = c.fetchall()
    return [dict(row) for row in rows]




def create_alert(rhino_id: str, alert_type: str, message: str) -> bool:
    """Create a new alert for a rhino."""
    try:
        with db_conn() as conn:
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO alerts (rhino_id, alert_type, message)
                VALUES (?, ?, ?)
            """,
                (rhino_id, alert_type, message),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def get_alerts(rhino_id: str = None, unresolved_only: bool = False) -> List[Dict]:
    """Get alerts, optionally filtered by rhino and resolution status."""
    query = "SELECT * FROM alerts WHERE 1=1"
    params = []

    if rhino_id:
        query += " AND rhino_id = ?"
        params.append(rhino_id)

    if unresolved_only:
        query += " AND resolved = 0"

    query += " ORDER BY created_at DESC"

    with db_conn() as conn:
        c = conn.cursor()
        c.execute(query, params)
        rows = c.fetchall()
    return [dict(row) for row in rows]


def resolve_alert(alert_id: int) -> bool:
    """Mark an alert as resolved."""
    try:
        with db_conn() as conn:
            c = conn.cursor()
            c.execute("UPDATE alerts SET resolved = 1 WHERE id = ?", (alert_id,))
            return c.rowcount > 0
    except Exception:
        return False
