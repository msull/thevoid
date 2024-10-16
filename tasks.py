from contextlib import contextmanager
from pathlib import Path

from invoke import Context, task


class Paths:
    here = Path(__file__).parent
    repo_root = here

    @staticmethod
    @contextmanager
    def cd(c: Context, p: Path):
        with c.cd(str(p)):
            yield


@task
def compile_requirements(c, upgrade=False):
    with Paths.cd(c, Paths.repo_root):
        upgrade_flag = "--upgrade" if upgrade else ""
        c.run(f"pip-compile --resolver=backtracking -v {upgrade_flag} -o requirements.txt")
