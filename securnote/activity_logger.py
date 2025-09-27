"""
Activity logging for SecurNote operations
Tracks user actions for admin monitoring
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .logging_config import get_logger

logger = get_logger("activity")


class ActivityLogger:
    """Logs user activities for admin monitoring."""

    def __init__(self, db_path: str = "data/activity.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize activity logging database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    username TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    success BOOLEAN NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON activities(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_username ON activities(username)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_action ON activities(action)
            """)

    def log_activity(
        self,
        username: str,
        action: str,
        success: bool,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
    ):
        """Log a user activity."""
        timestamp = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO activities
                (timestamp, username, action, details, ip_address, success)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (timestamp, username, action, details, ip_address, success),
            )

        # Also log to console/file
        status = "SUCCESS" if success else "FAILED"
        log_msg = f"USER_ACTIVITY: {username} {action} - {status}"
        if details:
            log_msg += f" ({details})"
        if ip_address:
            log_msg += f" from {ip_address}"

        logger.info(log_msg)

    def get_recent_activities(self, limit: int = 100) -> List[Dict]:
        """Get recent activities for admin panel."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT timestamp, username, action, details, ip_address, success
                FROM activities
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_user_activities(self, username: str, limit: int = 50) -> List[Dict]:
        """Get activities for specific user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT timestamp, action, details, ip_address, success
                FROM activities
                WHERE username = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (username, limit),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_activity_stats(self) -> Dict:
        """Get activity statistics."""
        with sqlite3.connect(self.db_path) as conn:
            # Total activities
            total = conn.execute("SELECT COUNT(*) FROM activities").fetchone()[0]

            # Recent activity (last 24 hours)
            since_yesterday = datetime.now().replace(hour=0, minute=0, second=0).isoformat()
            recent = conn.execute(
                "SELECT COUNT(*) FROM activities WHERE timestamp >= ?",
                (since_yesterday,)
            ).fetchone()[0]

            # Unique users
            unique_users = conn.execute(
                "SELECT COUNT(DISTINCT username) FROM activities"
            ).fetchone()[0]

            # Most active users (top 5)
            cursor = conn.execute("""
                SELECT username, COUNT(*) as activity_count
                FROM activities
                GROUP BY username
                ORDER BY activity_count DESC
                LIMIT 5
            """)
            top_users = [{"username": row[0], "count": row[1]} for row in cursor.fetchall()]

            # Action breakdown
            cursor = conn.execute("""
                SELECT action, COUNT(*) as count
                FROM activities
                GROUP BY action
                ORDER BY count DESC
            """)
            action_stats = [{"action": row[0], "count": row[1]} for row in cursor.fetchall()]

            return {
                "total_activities": total,
                "recent_activities": recent,
                "unique_users": unique_users,
                "top_users": top_users,
                "action_breakdown": action_stats
            }


# Global activity logger instance
activity_logger = ActivityLogger()