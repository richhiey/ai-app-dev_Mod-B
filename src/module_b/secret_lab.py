"""Disposable synthetic fixtures. No inspection of the learner's real repositories."""
from pathlib import Path
import subprocess
import tempfile

MARKER = 'SYNTHETIC_SECRET_MARKER_NOT_A_CREDENTIAL'


def marker_present(value):
    return MARKER in str(value)


def repository_rehearsal():
    """Observed Git ignore/history effects inside a newly created disposable repo."""
    with tempfile.TemporaryDirectory(prefix='fieldcare-fake-leak-') as temp:
        root=Path(temp)
        def git(*args):
            return subprocess.run(['git','-c','user.name=FieldCare synthetic lab',
                '-c','user.email=lab@example.invalid',*args],cwd=root,check=True,
                capture_output=True,text=True).stdout
        git('init','-q')
        (root/'.env').write_text('DEMO_MARKER='+MARKER+'\n')
        git('add','.env');git('commit','-qm','Synthetic fixture; no functional key')
        (root/'.gitignore').write_text('.env\n')
        tracked_after_ignore=bool(git('ls-files','.env').strip())
        git('rm','--cached','.env');git('add','.gitignore');git('commit','-qm','Stop tracking synthetic environment')
        tracked_after_remove=bool(git('ls-files','.env').strip())
        history_contains_marker=MARKER in git('show','HEAD~1:.env')
        return {'tracked_after_ignore':tracked_after_ignore,
                'tracked_after_remove':tracked_after_remove,
                'history_still_contains_marker':history_contains_marker,
                'real_credentials_used':False}
