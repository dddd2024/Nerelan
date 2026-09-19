"""Default test collection excludes integrations that launch installed tools."""


def pytest_addoption(parser):
    parser.addoption(
        "--run-installed-opencode",
        action="store_true",
        default=False,
        help="Collect installed OpenCode integrations; execution requires separate authorization.",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-installed-opencode"):
        return
    deselected = [item for item in items if item.get_closest_marker("installed_opencode")]
    if deselected:
        selected = [item for item in items if not item.get_closest_marker("installed_opencode")]
        config.hook.pytest_deselected(items=deselected)
        items[:] = selected
