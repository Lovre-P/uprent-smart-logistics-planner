import json
import os
from pathlib import Path
import subprocess

import pytest

from uprent.cli import main


ROOT = Path(__file__).resolve().parents[1]
DEFAULT = str(ROOT / "data" / "default_scenario.json")


def test_cli_json_default(capsys):
    assert main(["solve", DEFAULT, "--json"]) == 0
    output = capsys.readouterr()
    result = json.loads(output.out)
    assert not output.err
    assert result["totals"]["km"] == 182.2 and result["status"] == "OPTIMAL"


def test_cli_set_override(capsys):
    assert main(["solve", DEFAULT, "--json", "--set", "limit_includes_handling=true"]) == 0
    assert json.loads(capsys.readouterr().out)["totals"]["km"] == 200.1


def test_cli_repeated_set_json(capsys):
    assert main(["solve", DEFAULT, "--json", "--set", 'pinned_orders={"N04":"A"}',
                 "--set", "day_start=09:00"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["totals"]["km"] == 217.0 and result["settings"]["day_start"] == "09:00"
    assert result["settings"]["pinned_orders"] == {"N04": "A"}


def test_cli_solver_flag(capsys):
    assert main(["solve", DEFAULT, "--json", "--solver", "ortools"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["solver"] == "ortools" and result["optimality"] == "best_found"


def test_cli_invalid_file(tmp_path, capsys):
    for path in (tmp_path / "nedostaje.json", tmp_path / "nevaljan.json"):
        if path.name == "nevaljan.json":
            path.write_text("nije JSON", encoding="utf-8")
        assert main(["solve", str(path), "--json"]) == 2
        output = capsys.readouterr()
        assert not output.out and path.name in output.err and "pročitati" in output.err


@pytest.mark.parametrize("args", [
    ["solve", DEFAULT, "--set", "bez-vrijednosti"], ["solve", DEFAULT, "--solver", "kriv"],
    ["solve", DEFAULT, "--set", 'pinned_orders={'], ["solve", DEFAULT, "--set", "=12"],
    ["solve", DEFAULT, "--nedostupno"], ["solve"], ["nepoznato"], [],
])
def test_cli_invalid_arguments_return_two(args, capsys):
    assert main(args) == 2
    output = capsys.readouterr()
    assert not output.out and "Pogreška" in output.err and "Traceback" not in output.err


def test_cli_compare_table(capsys):
    assert main(["compare", DEFAULT]) == 0
    output = capsys.readouterr().out
    for label in ("Zadano (doslovno tumačenje)", "U 9 h ulazi utovar/istovar",
                  "Svaki kamion mora voziti", "9 h s utovarom, 20 min po nalogu",
                  "Najraniji završetak", "Jedan stroj odjednom"):
        assert label in output
    assert "182,2" in output and "samo vožnja" in output


def test_cli_text_plan_and_warnings(tmp_path, scenario_data, capsys):
    scenario_data["machines"].append({"id": "M11", "weight_kg": 12000})
    scenario_data["orders"].append({"id": "N11", "machine": "M11", "pickup": "L1", "delivery": "L3"})
    path = tmp_path / "nalog.json"
    path.write_text(json.dumps(scenario_data), encoding="utf-8")
    assert main(["solve", str(path)]) == 0
    out = capsys.readouterr().out
    for fragment in ("Kamion A", "Kamion B", "182,2 km", "10/11", "Utovar", "Istovar", "Povratak",
                     "Upozorenja", "N11", "12.000 kg"):
        assert fragment in out


def test_cli_help_is_croatian(capsys):
    assert main(["solve", "--help"]) == 0
    text = capsys.readouterr().out
    assert "Uporaba" in text and "--set" in text and "usage:" not in text


def test_installed_cli_writes_utf8_json():
    process = subprocess.run(
        ["uv", "run", "uprent", "solve", DEFAULT, "--json"], cwd=ROOT,
        env={**os.environ, "PYTHONIOENCODING": "cp1250"}, capture_output=True, check=True,
        timeout=35,
    )
    result = json.loads(process.stdout.decode("utf-8", errors="strict"))
    assert result["validation"]["passed"] and result["totals"]["km"] == 182.2
    assert "vožnj" in process.stdout.decode("utf-8").lower()
