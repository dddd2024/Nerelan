import pytest

from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.platform_v1.history_query import (
    ACTIVE, ALL, ARCHIVED, CREATED_DESC, GOAL, RUN, UPDATED_DESC,
    HistoryQueryError, HistoryQueryService,
)
from reverse_agent.platform_v1.run_store import TaskStore


@pytest.fixture
def hq():
    store = TaskStore(":memory:")
    control = PlatformControlStore(store)
    service = HistoryQueryService(store=store, control_store=control)
    yield store, control, service
    store._conn.close()


def set_goal(store, ident, *, status=None, created=None, updated=None, repository=None, executor=None):
    parts = []
    vals = []
    for col, val in (("status", status), ("created_at", created), ("updated_at", updated), ("repository", repository), ("executor_kind", executor)):
        if val is not None:
            parts.append(f"{col}=?")
            vals.append(val)
    if parts:
        vals.append(ident)
        store._conn.execute("UPDATE platform_goals SET " + ",".join(parts) + " WHERE id=?", vals)


def set_task(store, ident, *, status=None, created=None, updated=None, repository=None, executor=None):
    parts = []
    vals = []
    for col, val in (("status", status), ("created_at", created), ("updated_at", updated), ("repository", repository), ("executor_kind", executor)):
        if val is not None:
            parts.append(f"{col}=?")
            vals.append(val)
    if parts:
        vals.append(ident)
        store._conn.execute("UPDATE tasks SET " + ",".join(parts) + " WHERE id=?", vals)


def test_basic_goal_and_run_query(hq):
    store, control, service = hq
    g = control.create_goal(title="Alpha", objective="secret objective", repository="owner/repo", executor_kind="opencode")
    t = store.create_task(title="Run Alpha", repository="owner/repo", executor_kind="opencode")
    gp = service.query(GOAL)
    rp = service.query(RUN)
    assert [x.id for x in gp.items] == [g.id]
    assert [x.id for x in rp.items] == [t.id]
    assert set(gp.items[0].__dict__) == {
        "kind", "id", "title", "repository", "status", "executor_kind",
        "orchestration_mode", "created_at", "updated_at", "archived", "archived_at",
    }


def test_literal_search_and_casefold(hq):
    store, control, service = hq
    g1 = control.create_goal(title="Needle%_X", objective="HiddenNeedle", repository="Owner/Repo")
    control.create_goal(title="NeedleABC", objective="x", repository="other/repo")
    assert [x.id for x in service.query(GOAL, text="needle%_").items] == [g1.id]
    assert [x.id for x in service.query(GOAL, text="OWNER/REPO").items] == [g1.id]
    assert service.query(GOAL, text="HiddenNeedle").items == ()


def test_status_repository_executor_and_date_filters(hq):
    store, control, service = hq
    g1 = control.create_goal(title="A", objective="x", repository="owner/a", executor_kind="opencode")
    g2 = control.create_goal(title="B", objective="x", repository="owner/b", executor_kind="fixture")
    set_goal(store, g1.id, status="COMPLETED", created="2026-09-10T00:00:00Z")
    set_goal(store, g2.id, status="BLOCKED", created="2026-09-11T00:00:00Z")
    assert [x.id for x in service.query(GOAL, statuses=["COMPLETED"]).items] == [g1.id]
    assert [x.id for x in service.query(GOAL, repositories=["owner/b"]).items] == [g2.id]
    assert [x.id for x in service.query(GOAL, executors=["opencode"]).items] == [g1.id]
    assert [x.id for x in service.query(GOAL, created_from_utc="2026-09-11T00:00:00Z").items] == [g2.id]
    assert [x.id for x in service.query(GOAL, created_to_utc="2026-09-10T00:00:00Z").items] == [g1.id]


def test_sort_and_cursor_no_duplicates(hq):
    store, control, service = hq
    ids = []
    for i in range(6):
        g = control.create_goal(title=f"G{i}", objective="x", repository="owner/repo")
        ids.append(g.id)
        set_goal(store, g.id, created="2026-09-01T00:00:00Z", updated=f"2026-09-0{1+i}T00:00:00Z")
    expected = sorted(ids, reverse=True)
    cursor = None
    seen = []
    while True:
        page = service.query(GOAL, sort=CREATED_DESC, limit=2, cursor=cursor)
        seen += [x.id for x in page.items]
        cursor = page.next_cursor
        if cursor is None:
            break
    assert seen == expected
    up = [x.id for x in service.query(GOAL, sort=UPDATED_DESC, limit=100).items]
    assert up == list(reversed(ids))


def test_cursor_binds_filters(hq):
    store, control, service = hq
    for i in range(3):
        g = control.create_goal(title=f"G{i}", objective="x", repository="owner/repo")
        set_goal(store, g.id, status="COMPLETED", created="2026-09-01T00:00:00Z")
    page = service.query(GOAL, statuses=["COMPLETED"], limit=1)
    assert page.next_cursor
    with pytest.raises(HistoryQueryError, match="invalid_history_cursor"):
        service.query(GOAL, statuses=["BLOCKED"], limit=1, cursor=page.next_cursor)


def test_newer_record_after_page_does_not_duplicate_seen(hq):
    store, control, service = hq
    for i in range(4):
        g = control.create_goal(title=f"G{i}", objective="x", repository="owner/repo")
        set_goal(store, g.id, created="2026-09-01T00:00:00Z")
    first = service.query(GOAL, limit=2)
    new = control.create_goal(title="New", objective="x", repository="owner/repo")
    set_goal(store, new.id, created="2026-09-12T00:00:00Z")
    second = service.query(GOAL, limit=2, cursor=first.next_cursor)
    assert not ({x.id for x in first.items} & {x.id for x in second.items})
    assert new.id not in {x.id for x in second.items}


def test_archive_views_and_idempotency_preserve_truth(hq):
    store, control, service = hq
    g = control.create_goal(title="Done", objective="x", repository="owner/repo")
    t = store.create_task(title="Failed", repository="owner/repo")
    set_goal(store, g.id, status="COMPLETED", updated="2026-09-10T00:00:00Z")
    set_task(store, t.id, status="FAILED", updated="2026-09-11T00:00:00Z")
    before_g = store._conn.execute("SELECT status,updated_at FROM platform_goals WHERE id=?", (g.id,)).fetchone()
    before_t = store._conn.execute("SELECT status,updated_at FROM tasks WHERE id=?", (t.id,)).fetchone()
    m1 = service.archive(GOAL, g.id)
    m2 = service.archive(GOAL, g.id)
    assert m1 == m2 and service.is_archived(GOAL, g.id)
    service.archive(RUN, t.id)
    assert service.query(GOAL, archive_view=ACTIVE).items == ()
    assert [x.id for x in service.query(GOAL, archive_view=ARCHIVED).items] == [g.id]
    assert service.query(GOAL, archive_view=ALL).items[0].archived is True
    assert service.unarchive(GOAL, g.id) is True
    assert service.unarchive(GOAL, g.id) is False
    after_g = store._conn.execute("SELECT status,updated_at FROM platform_goals WHERE id=?", (g.id,)).fetchone()
    after_t = store._conn.execute("SELECT status,updated_at FROM tasks WHERE id=?", (t.id,)).fetchone()
    assert tuple(before_g) == tuple(after_g)
    assert tuple(before_t) == tuple(after_t)


@pytest.mark.parametrize("kind,status", [
    (GOAL, "DRAFT"), (GOAL, "RUNNING"), (RUN, "QUEUED"), (RUN, "INTERRUPTED"),
])
def test_nonterminal_archive_fails(hq, kind, status):
    store, control, service = hq
    if kind == GOAL:
        record = control.create_goal(title="x", objective="x", repository="owner/repo")
        set_goal(store, record.id, status=status)
    else:
        record = store.create_task(title="x")
        set_task(store, record.id, status=status)
    with pytest.raises(HistoryQueryError, match="history_subject_not_archivable"):
        service.archive(kind, record.id)


def test_missing_archive_subject_fails(hq):
    with pytest.raises(HistoryQueryError, match="history_subject_not_found"):
        hq[2].archive(GOAL, "goal-missing")


def test_reads_zero_write(hq):
    store, control, service = hq
    g = control.create_goal(title="Done", objective="x", repository="owner/repo")
    set_goal(store, g.id, status="COMPLETED")
    service.archive(GOAL, g.id)
    writes = store._conn.total_changes
    service.query(GOAL, archive_view=ALL)
    service.is_archived(GOAL, g.id)
    assert store._conn.total_changes == writes


@pytest.mark.parametrize("kwargs", [
    {"kind": "bad"},
    {"kind": GOAL, "statuses": ["NOPE"]},
    {"kind": GOAL, "archive_view": "bad"},
    {"kind": GOAL, "sort": "bad"},
    {"kind": GOAL, "limit": 0},
    {"kind": GOAL, "limit": 101},
    {"kind": GOAL, "text": "x" * 257},
    {"kind": GOAL, "created_from_utc": "2026-09-01"},
    {"kind": GOAL, "created_from_utc": "2026-09-12T00:00:00Z", "created_to_utc": "2026-09-01T00:00:00Z"},
    {"kind": GOAL, "repositories": [f"r{i}" for i in range(21)]},
])
def test_invalid_queries_fail_closed(hq, kwargs):
    kind = kwargs.pop("kind")
    with pytest.raises(HistoryQueryError):
        hq[2].query(kind, **kwargs)


def test_invalid_cursor_fails(hq):
    with pytest.raises(HistoryQueryError, match="invalid_history_cursor"):
        hq[2].query(GOAL, cursor="not!base64")


def test_active_transaction_archive_fails_without_touching_caller_tx(hq):
    store, control, service = hq
    g = control.create_goal(title="Done", objective="x", repository="owner/repo")
    set_goal(store, g.id, status="COMPLETED")
    store._conn.execute("BEGIN")
    store._conn.execute("UPDATE platform_goals SET title='caller edit' WHERE id=?", (g.id,))
    with pytest.raises(HistoryQueryError, match="history_archive_during_active_transaction"):
        service.archive(GOAL, g.id)
    assert store._conn.in_transaction
    assert store._conn.execute("SELECT title FROM platform_goals WHERE id=?", (g.id,)).fetchone()[0] == "caller edit"
    store._conn.execute("ROLLBACK")


def test_file_backed_two_connections_share_archive(tmp_path):
    path = str(tmp_path / "state.sqlite3")
    s1 = TaskStore(path)
    c1 = PlatformControlStore(s1)
    q1 = HistoryQueryService(store=s1, control_store=c1)
    g = c1.create_goal(title="Done", objective="x", repository="owner/repo")
    set_goal(s1, g.id, status="COMPLETED")
    s2 = TaskStore(path)
    c2 = PlatformControlStore(s2)
    q2 = HistoryQueryService(store=s2, control_store=c2)
    try:
        q1.archive(GOAL, g.id)
        assert q2.is_archived(GOAL, g.id)
        assert [x.id for x in q2.query(GOAL, archive_view=ARCHIVED).items] == [g.id]
    finally:
        s2._conn.close()
        s1._conn.close()


def test_orphan_archive_does_not_fabricate_record(hq):
    store, _, service = hq
    store._conn.execute(
        "INSERT INTO platform_history_archive VALUES('GOAL','missing','2026-09-12T00:00:00Z')"
    )
    assert service.query(GOAL, archive_view=ARCHIVED).items == ()
