"""
Serie A Tournament - Database Layer
All SQLite operations in one place. The rest of the app never touches SQL directly.
"""

import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tournament.db")


@contextmanager
def get_conn():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create tables if they don't exist."""
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                gender TEXT NOT NULL CHECK(gender IN ('M', 'F')),
                active INTEGER NOT NULL DEFAULT 1,
                deleted INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                round_number INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                round_id INTEGER NOT NULL,
                court_number INTEGER NOT NULL,
                team1_p1 INTEGER NOT NULL,
                team1_p2 INTEGER NOT NULL,
                team2_p1 INTEGER NOT NULL,
                team2_p2 INTEGER NOT NULL,
                winner INTEGER CHECK(winner IN (1, 2)),
                FOREIGN KEY (round_id) REFERENCES rounds(id) ON DELETE CASCADE,
                FOREIGN KEY (team1_p1) REFERENCES players(id),
                FOREIGN KEY (team1_p2) REFERENCES players(id),
                FOREIGN KEY (team2_p1) REFERENCES players(id),
                FOREIGN KEY (team2_p2) REFERENCES players(id)
            );
        """)


# ---------------------------------------------------------------------------
# Players
# ---------------------------------------------------------------------------

def add_player(name: str, gender: str) -> int:
    """Add a player. Returns the new player's id."""
    with get_conn() as conn:
        cursor = conn.execute(
            "INSERT INTO players (name, gender) VALUES (?, ?)",
            (name.strip(), gender.upper()),
        )
        return cursor.lastrowid


def update_player(player_id: int, name: str = None, gender: str = None):
    """Update a player's name and/or gender."""
    with get_conn() as conn:
        if name is not None:
            conn.execute("UPDATE players SET name = ? WHERE id = ?", (name.strip(), player_id))
        if gender is not None:
            conn.execute("UPDATE players SET gender = ? WHERE id = ?", (gender.upper(), player_id))


def soft_delete_player(player_id: int):
    """Soft-delete a player (preserves history)."""
    with get_conn() as conn:
        conn.execute("UPDATE players SET deleted = 1, active = 0 WHERE id = ?", (player_id,))


def set_player_active(player_id: int, active: bool):
    """Toggle a player's active status."""
    with get_conn() as conn:
        conn.execute("UPDATE players SET active = ? WHERE id = ?", (int(active), player_id))


def set_all_players_active(active: bool):
    """Set all non-deleted players to active or inactive."""
    with get_conn() as conn:
        conn.execute("UPDATE players SET active = ? WHERE deleted = 0", (int(active),))


def reset_tournament():
    """Wipe everything — players, rounds, matches. Full fresh start."""
    with get_conn() as conn:
        conn.executescript("""
            DELETE FROM matches;
            DELETE FROM rounds;
            DELETE FROM players;
        """)


def get_all_players() -> list[dict]:
    """Get all non-deleted players."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, name, gender, active FROM players WHERE deleted = 0 ORDER BY name"
        ).fetchall()
        return [dict(r) for r in rows]


def get_active_players() -> list[dict]:
    """Get all active, non-deleted players."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, name, gender, active FROM players WHERE active = 1 AND deleted = 0 ORDER BY name"
        ).fetchall()
        return [dict(r) for r in rows]



# ---------------------------------------------------------------------------
# Rounds
# ---------------------------------------------------------------------------

def create_round() -> int:
    """Create a new round. Returns the round id."""
    with get_conn() as conn:
        # Determine next round number
        row = conn.execute("SELECT COALESCE(MAX(round_number), 0) FROM rounds").fetchone()
        next_number = row[0] + 1
        cursor = conn.execute(
            "INSERT INTO rounds (round_number) VALUES (?)", (next_number,)
        )
        return cursor.lastrowid


def get_current_round() -> dict | None:
    """Get the latest round, or None if no rounds exist."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, round_number, created_at FROM rounds ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None


def get_round_count() -> int:
    """Get total number of rounds played."""
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) FROM rounds").fetchone()
        return row[0]


def delete_round(round_id: int):
    """Delete a round and all its matches (CASCADE). This is our 'undo'."""
    with get_conn() as conn:
        conn.execute("DELETE FROM rounds WHERE id = ?", (round_id,))


# ---------------------------------------------------------------------------
# Matches
# ---------------------------------------------------------------------------

def create_match(round_id: int, court_number: int,
                 team1_p1: int, team1_p2: int,
                 team2_p1: int, team2_p2: int) -> int:
    """Create a match. Returns the match id."""
    with get_conn() as conn:
        cursor = conn.execute(
            """INSERT INTO matches (round_id, court_number, team1_p1, team1_p2, team2_p1, team2_p2)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (round_id, court_number, team1_p1, team1_p2, team2_p1, team2_p2),
        )
        return cursor.lastrowid


def record_result(match_id: int, winner: int):
    """Record a match result. winner is 1 or 2."""
    with get_conn() as conn:
        conn.execute("UPDATE matches SET winner = ? WHERE id = ?", (winner, match_id))


def clear_result(match_id: int):
    """Clear a match result (set winner back to NULL)."""
    with get_conn() as conn:
        conn.execute("UPDATE matches SET winner = NULL WHERE id = ?", (match_id,))


def get_matches_for_round(round_id: int) -> list[dict]:
    """Get all matches in a round with player names."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT
                m.id, m.court_number, m.winner,
                m.team1_p1, m.team1_p2, m.team2_p1, m.team2_p2,
                p1.name as t1p1_name, p1.gender as t1p1_gender,
                p2.name as t1p2_name, p2.gender as t1p2_gender,
                p3.name as t2p1_name, p3.gender as t2p1_gender,
                p4.name as t2p2_name, p4.gender as t2p2_gender
            FROM matches m
            JOIN players p1 ON m.team1_p1 = p1.id
            JOIN players p2 ON m.team1_p2 = p2.id
            JOIN players p3 ON m.team2_p1 = p3.id
            JOIN players p4 ON m.team2_p2 = p4.id
            WHERE m.round_id = ?
            ORDER BY m.court_number""",
            (round_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def round_is_complete(round_id: int) -> bool:
    """Check if all matches in a round have results."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM matches WHERE round_id = ? AND winner IS NULL",
            (round_id,),
        ).fetchone()
        return row[0] == 0


def round_has_any_results(round_id: int) -> bool:
    """Check if any match in a round has a result recorded."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM matches WHERE round_id = ? AND winner IS NOT NULL",
            (round_id,),
        ).fetchone()
        return row[0] > 0


# ---------------------------------------------------------------------------
# Statistics & History (derived data)
# ---------------------------------------------------------------------------

def get_leaderboard() -> list[dict]:
    """
    Get leaderboard: each player's total wins and games played.
    Sorted by wins descending, then games ascending (fewer games = more impressive).
    """
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT
                p.id, p.name, p.gender,
                COUNT(m.id) as games_played,
                SUM(CASE
                    WHEN (m.winner = 1 AND p.id IN (m.team1_p1, m.team1_p2)) THEN 1
                    WHEN (m.winner = 2 AND p.id IN (m.team2_p1, m.team2_p2)) THEN 1
                    ELSE 0
                END) as wins
            FROM players p
            LEFT JOIN matches m ON p.id IN (m.team1_p1, m.team1_p2, m.team2_p1, m.team2_p2)
                AND m.winner IS NOT NULL
            WHERE p.deleted = 0
            GROUP BY p.id
            HAVING games_played > 0
            ORDER BY wins DESC, games_played ASC"""
        ).fetchall()
        return [dict(r) for r in rows]


def get_games_played_counts() -> dict[int, int]:
    """Get number of games played per player (for balancing). Includes all matches, even unfinished."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT p.id, COUNT(m.id) as games
            FROM players p
            LEFT JOIN matches m ON p.id IN (m.team1_p1, m.team1_p2, m.team2_p1, m.team2_p2)
            WHERE p.deleted = 0
            GROUP BY p.id"""
        ).fetchall()
        return {r["id"]: r["games"] for r in rows}


def get_wins_counts() -> dict[int, int]:
    """Get total wins per player (for skill balancing)."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT p.id,
                SUM(CASE
                    WHEN (m.winner = 1 AND p.id IN (m.team1_p1, m.team1_p2)) THEN 1
                    WHEN (m.winner = 2 AND p.id IN (m.team2_p1, m.team2_p2)) THEN 1
                    ELSE 0
                END) as wins
            FROM players p
            LEFT JOIN matches m ON p.id IN (m.team1_p1, m.team1_p2, m.team2_p1, m.team2_p2)
                AND m.winner IS NOT NULL
            WHERE p.deleted = 0
            GROUP BY p.id"""
        ).fetchall()
        return {r["id"]: r["wins"] for r in rows}


def get_past_partners(player_id: int) -> set[int]:
    """Get set of player IDs this player has been partnered with."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT DISTINCT
                CASE
                    WHEN team1_p1 = ? THEN team1_p2
                    WHEN team1_p2 = ? THEN team1_p1
                    WHEN team2_p1 = ? THEN team2_p2
                    WHEN team2_p2 = ? THEN team2_p1
                END as partner_id
            FROM matches
            WHERE ? IN (team1_p1, team1_p2, team2_p1, team2_p2)""",
            (player_id, player_id, player_id, player_id, player_id),
        ).fetchall()
        return {r["partner_id"] for r in rows if r["partner_id"] is not None}


def get_past_opponents(player_id: int) -> dict[int, int]:
    """
    Get how many times this player has faced each opponent.
    Returns {opponent_id: count}.
    """
    with get_conn() as conn:
        # When player is on team 1, opponents are team 2
        rows_as_t1 = conn.execute(
            """SELECT team2_p1 as opp_id FROM matches WHERE ? IN (team1_p1, team1_p2)
               UNION ALL
               SELECT team2_p2 as opp_id FROM matches WHERE ? IN (team1_p1, team1_p2)""",
            (player_id, player_id),
        ).fetchall()
        # When player is on team 2, opponents are team 1
        rows_as_t2 = conn.execute(
            """SELECT team1_p1 as opp_id FROM matches WHERE ? IN (team2_p1, team2_p2)
               UNION ALL
               SELECT team1_p2 as opp_id FROM matches WHERE ? IN (team2_p1, team2_p2)""",
            (player_id, player_id),
        ).fetchall()

        counts: dict[int, int] = {}
        for r in rows_as_t1 + rows_as_t2:
            opp = r["opp_id"]
            counts[opp] = counts.get(opp, 0) + 1
        return counts


def get_all_past_partnerships() -> set[tuple[int, int]]:
    """Get all past partner pairs as a set of (id1, id2) tuples where id1 < id2."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT team1_p1, team1_p2 FROM matches
               UNION ALL
               SELECT team2_p1, team2_p2 FROM matches"""
        ).fetchall()
        pairs = set()
        for r in rows:
            a, b = r[0], r[1]
            pairs.add((min(a, b), max(a, b)))
        return pairs


def get_all_past_opponents() -> dict[tuple[int, int], int]:
    """
    Get all past opponent pairings with counts.
    Returns {(id1, id2): count} where id1 < id2.
    """
    with get_conn() as conn:
        # All opponent pairs from team1 vs team2
        rows = conn.execute(
            """SELECT team1_p1, team2_p1 FROM matches
               UNION ALL SELECT team1_p1, team2_p2 FROM matches
               UNION ALL SELECT team1_p2, team2_p1 FROM matches
               UNION ALL SELECT team1_p2, team2_p2 FROM matches"""
        ).fetchall()
        counts: dict[tuple[int, int], int] = {}
        for r in rows:
            pair = (min(r[0], r[1]), max(r[0], r[1]))
            counts[pair] = counts.get(pair, 0) + 1
        return counts