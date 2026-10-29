"""Keep docs pushes separate from guarded package publication."""

import re
from fnmatch import fnmatchcase
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = "ed8ea8ac5989cbc883c149843b311aeecb44e6a2"


def _workflow(name):
    return yaml.safe_load((ROOT / ".github/workflows" / name).read_text())


def _push_matches(workflow, ref):
    # PyYAML's YAML 1.1 reader represents the Actions "on" key as True.
    push = workflow[True]["push"]
    kind, name = ref.removeprefix("refs/").split("/", 1)
    filters = push.get({"heads": "branches", "tags": "tags"}[kind], [])
    return any(fnmatchcase(name, pattern) for pattern in filters)


def test_release_hook_inherits_catalogue_policy():
    config = yaml.safe_load((ROOT / ".pre-commit-config.yaml").read_text())
    matches = [
        (repo, hook)
        for repo in config["repos"]
        for hook in repo["hooks"]
        if hook["id"] == "dependency-readiness"
    ]
    assert len(matches) == 1
    repo, hook = matches[0]
    assert repo["repo"] == "https://github.com/Knuckles-Team/pipelines"
    assert re.fullmatch(r"[0-9a-f]{40}", repo["rev"])
    assert hook == {"id": "dependency-readiness"}


def test_alternate_docs_job_keeps_validation_without_publication():
    workflow = _workflow("docs.yml")
    assert workflow[True] == {
        "push": {"branches": ["main"]},
        "workflow_dispatch": None,
    }
    assert workflow["permissions"] == {"contents": "write"}
    assert set(workflow["jobs"]) == {"deploy-docs"}
    job = workflow["jobs"]["deploy-docs"]
    assert job["runs-on"] == "ubuntu-latest"
    assert [step.get("run") for step in job["steps"] if "run" in step] == [
        "pip install mkdocs-material",
        "mkdocs build",
    ]
    assert all(
        "gh-deploy" not in path.read_text()
        for path in (ROOT / ".github/workflows").glob("*.yml")
    )
