"""Keep docs pushes separate from guarded package publication."""

from fnmatch import fnmatchcase
from pathlib import Path

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
    assert repo["rev"] == "main"
    assert hook == {"id": "dependency-readiness"}


def test_docs_build_and_publication_belong_to_the_standard_connector_workflow():
    workflows = {path.name for path in (ROOT / ".github/workflows").glob("*.yml")}
    assert workflows == {"connector.yml"}
    workflow = _workflow("connector.yml")
    assert workflow["jobs"]["pipeline"]["uses"] == (
        "Knuckles-Team/pipelines/.github/workflows/connector_pipeline.yml@main"
    )
    assert _push_matches(workflow, "refs/tags/v1.2.3")
    assert all(
        "gh-deploy" not in path.read_text()
        for path in (ROOT / ".github/workflows").glob("*.yml")
    )
