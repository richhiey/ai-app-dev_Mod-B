from pathlib import Path
import pytest
from module_b.secret_workshop import prepare_secret_workshop, inspect_secret_workshop, git_fixture

REPO=Path(__file__).resolve().parents[1]

def test_applied_preventions_survive_new_marker_and_preserve_useful_content(tmp_path):
    for label in ('FIRST','FRESH'):
        root=prepare_secret_workshop(tmp_path/label,marker=f'SYNTHETIC_{label}_NOT_A_CREDENTIAL',repo_root=REPO)
        before=inspect_secret_workshop(root)
        assert not before['passed']
        assert not before['checks']['ordinary_log_excludes_marker']
        assert not before['checks']['exception_log_excludes_marker']
        assert not before['checks']['prompt_excludes_marker']
        assert not before['checks']['new_local_file_ignored']
        for name in ('log','prompt'):
            (root/f'{name}_policy.py').write_text((REPO/f'examples/patterns/secret_workshop/{name}_safe.py').read_text())
        (root/'.gitignore').write_text('.env\nlocal.key\n')
        # An ignore rule alone cannot untrack the already committed .env.
        assert not inspect_secret_workshop(root)['checks']['environment_untracked']
        git_fixture(root,'rm','--cached','.env')
        report=inspect_secret_workshop(root)
        assert report['passed']
        assert report['checks']['historical_exposure_still_visible']
        # Reopening the fixture must retain all learner edits.
        prepare_secret_workshop(root,marker=f'SYNTHETIC_{label}_NOT_A_CREDENTIAL',repo_root=REPO)
        assert inspect_secret_workshop(root)==report

def test_fixture_refuses_unmarked_directory_or_changed_marker(tmp_path):
    with pytest.raises(ValueError):git_fixture(tmp_path,'status')
    with pytest.raises(ValueError):prepare_secret_workshop(tmp_path/'bad',marker='usable-looking-value')
    root=prepare_secret_workshop(tmp_path/'good',marker='SYNTHETIC_FIRST_NOT_A_CREDENTIAL',repo_root=REPO)
    with pytest.raises(ValueError):prepare_secret_workshop(root,marker='SYNTHETIC_SECOND_NOT_A_CREDENTIAL',repo_root=REPO)
