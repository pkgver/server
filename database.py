import os
import sqlite3

DATABASE_PATH = os.path.join(os.path.dirname(__file__), "versions.db")

conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
c = conn.cursor()


def query(statement: str, *args):
    with conn:
        if "select" in statement.lower():
            c.execute(statement, args)
            result = c.fetchall()
        else:
            c.execute("PRAGMA foreign_keys = ON")
            c.execute(statement, args)
            result = c.rowcount
    return result


def create_db():
    with conn:
        c.executescript(
            """
            CREATE TABLE version (
                package TEXT,
                version TEXT,
                commit_hash TEXT NOT NULL,
                timestamp DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now', 'localtime')),
                PRIMARY KEY (package, version)
            );
            """
        )


def mock_data():
    versions = [('jq', '1.5', '64e550c31f9119cb3e9335c83a5663d8c6bb71e0'),
                ('jq', '1.6', 'aae20cf5c05f9478c1933471f2ac1e841376eb91'),
                ('bat', '0.22.0', '43bf7f32c1016486f72159e0deeabc8383c191d1'),
                ('bat', '0.22.1', 'd97726bb767167a9baf67979bd37b3a1d45aa83e')]

    for version in versions:
        package, version, commit_hash = version
        query('INSERT INTO version(package, version, commit_hash) VALUES (?, ?, ?)', package, version, commit_hash)


if __name__ == '__main__':
    create_db()
