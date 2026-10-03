import subprocess

import pytest

from module_b.secret_workshop import prepare_secret_workshop


def test_fixture_has_explicit_synthetic_marker_and_local_git_history(tmp_path):
    marker = "SYNTHETIC_TEST_RUN_NOT_A_CREDENTIAL"
    fixture = prepare_secret_workshop(
        tmp_path / "fixture", marker=marker
    )

    assert (fixture / ".env").read_text() == f"FAKE_MARKER={marker}\n"
    assert (fixture / "local.key").read_text() == f"{marker}\n"
    historical_env = subprocess.run(
        ["git", "-C", str(fixture), "show", "HEAD:.env"],
        check=True, capture_output=True, text=True,
    ).stdout
    assert historical_env == f"FAKE_MARKER={marker}\n"
    assert (fixture / "log_policy.py").is_file()
    assert (fixture / "prompt_policy.py").is_file()


def test_same_fixture_rerun_preserves_learner_edits(tmp_path):
    marker = "SYNTHETIC_TEST_RUN_NOT_A_CREDENTIAL"
    fixture = prepare_secret_workshop(
        tmp_path / "fixture", marker=marker
    )
    policy = fixture / "log_policy.py"
    policy.write_text("learner edit\n")

    assert prepare_secret_workshop(
        fixture, marker=marker
    ) == fixture
    assert policy.read_text() == "learner edit\n"


def test_fixture_refuses_a_marker_that_could_be_mistaken_for_a_secret(tmp_path):
    with pytest.raises(ValueError, match="synthetic marker"):
        prepare_secret_workshop(
            tmp_path / "fixture", marker="actual-looking-secret"
        )
