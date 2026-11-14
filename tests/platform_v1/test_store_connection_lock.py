"""TaskStore's shared connection is serialized for every caller (#1528).

Callers across the host reach ``store._conn`` directly from HTTP handler,
dispatcher and executor threads. Unserialized use of one ``sqlite3``
connection returned rows with NULL/swapped values and crashed the host
natively, so the connection itself must take the store lock.
"""

from __future__ import annotations

import json
import threading
import time

from reverse_agent.platform_v1.run_store import TaskStore


def _store(tmp_path):
    store = TaskStore(str(tmp_path / "tasks.sqlite3"))
    store._conn.execute("CREATE TABLE probe(id INTEGER PRIMARY KEY, body TEXT NOT NULL)")
    for index in range(100):
        store._conn.execute("INSERT INTO probe(body) VALUES (?)",
                            (json.dumps({"n": index, "text": "x" * (40 + index)}),))
    return store


def test_unlocked_callers_on_many_threads_read_consistent_rows(tmp_path):
    store = _store(tmp_path)
    errors: list[BaseException] = []
    reads = [0]
    deadline = time.monotonic() + 2.0

    def reader():
        try:
            while time.monotonic() < deadline:
                rows = store._conn.execute("SELECT body FROM probe ORDER BY random() LIMIT 20").fetchall()
                for row in rows:
                    assert isinstance(json.loads(row["body"])["n"], int)
                for row in store._conn.execute("SELECT id, body FROM probe LIMIT 5"):
                    assert row["body"] is not None
                reads[0] += 1
        except BaseException as exc:  # noqa: BLE001 - surfaced below
            errors.append(exc)

    def writer():
        index = 0
        try:
            while time.monotonic() < deadline:
                index += 1
                cursor = store._conn.cursor()
                cursor.execute("UPDATE probe SET body=? WHERE id=?",
                               (json.dumps({"n": index, "text": "y" * (index % 200)}), index % 100 + 1))
        except BaseException as exc:  # noqa: BLE001 - surfaced below
            errors.append(exc)

    threads = [threading.Thread(target=reader) for _ in range(4)] + [threading.Thread(target=writer) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    assert reads[0] > 0


def test_direct_connection_use_waits_for_the_store_lock(tmp_path):
    store = _store(tmp_path)
    finished = threading.Event()

    def query():
        store._conn.execute("SELECT count(*) FROM probe").fetchone()
        finished.set()

    with store._lock:
        thread = threading.Thread(target=query)
        thread.start()
        assert not finished.wait(0.3)
    assert finished.wait(5)
    thread.join()


def test_connection_context_manager_and_passthrough_still_work(tmp_path):
    store = _store(tmp_path)
    with store._conn:
        store._conn.execute("BEGIN IMMEDIATE")
        assert store._conn.in_transaction
        store._conn.execute("DELETE FROM probe WHERE id = 1")
    assert not store._conn.in_transaction
    cursor = store._conn.execute("SELECT count(*) AS n FROM probe")
    assert cursor.fetchone()["n"] == 99
    assert store._conn.execute("UPDATE probe SET body = body WHERE id = 2").rowcount == 1
