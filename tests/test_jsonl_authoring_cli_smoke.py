from __future__ import annotations

import json
from pathlib import Path

from sap_agent_context.agent_records import RECORD_FILES, export_agent_records
from sap_agent_context.cli import main
from sap_agent_context.repository import load_items

ROOT = Path(__file__).resolve().parents[1]


def _copy_minimal_records(records_dir: Path) -> None:
    exported = records_dir / "exported"
    export_agent_records(load_items(ROOT), exported, root=ROOT)
    records_dir.mkdir(parents=True, exist_ok=True)
    for filename in RECORD_FILES.values():
        source = exported / filename
        lines = source.read_text(encoding="utf-8").splitlines()
        first_record = next(line for line in lines if line)
        (records_dir / filename).write_text(first_record + "\n", encoding="utf-8")


def test_validate_records_cli_accepts_small_jsonl_authoring_fixture(tmp_path: Path, capsys) -> None:
    records_dir = tmp_path / "records"
    _copy_minimal_records(records_dir)

    exit_code = main(["--root", str(ROOT), "validate-records", "--records-dir", str(records_dir)])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["status"] == "passed"
    assert payload["files"] == len(RECORD_FILES)
    assert payload["records_dir"] == str(records_dir)


def test_validate_records_cli_reports_actionable_record_id_and_path(
    tmp_path: Path, capsys
) -> None:
    records_dir = tmp_path / "records"
    _copy_minimal_records(records_dir)
    apps_path = records_dir / "apps.jsonl"
    app = json.loads(apps_path.read_text(encoding="utf-8").splitlines()[0])
    app["access"] = "customer_private"
    apps_path.write_text(json.dumps(app, sort_keys=True) + "\n", encoding="utf-8")

    exit_code = main(["--root", str(ROOT), "validate-records", "--records-dir", str(records_dir)])

    payload = json.loads(capsys.readouterr().out)
    issue = payload["issues"][0]
    assert exit_code == 1
    assert payload["status"] == "failed"
    assert issue["path"] == str(apps_path)
    assert issue["id"] == app["id"]
    assert app["id"] in issue["message"]
    assert "access" in issue["message"]
