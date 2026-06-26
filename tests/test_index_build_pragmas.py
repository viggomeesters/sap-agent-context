from __future__ import annotations

import sqlite3

from sap_agent_context.index import _configure_build_connection


def test_configure_build_connection_uses_fast_rebuildable_pragmas() -> None:
    with sqlite3.connect(":memory:") as conn:
        _configure_build_connection(conn)
        synchronous = conn.execute("PRAGMA synchronous").fetchone()[0]
        temp_store = conn.execute("PRAGMA temp_store").fetchone()[0]

    assert synchronous == 0
    assert temp_store == 2
