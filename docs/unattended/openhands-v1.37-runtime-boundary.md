# OpenHands v1.37.0 runtime-boundary evidence

This evidence is fixed to:

- upstream tag `v1.37.0`;
- upstream commit `c248ec0aefa17a7e4776b5b6e65e4e7866cc780a`;
- image
  `ghcr.io/openhands/agent-server:1.37.0-python@sha256:c188dac7624d486331b455042d54abe020af43b843c2c02694deccecfbed487a`.

It does not infer isolation from prompts or from the absence of a Docker CLI.

## Actual tool execution

The pinned source establishes the following:

- `openhands-sdk/openhands/sdk/workspace/local.py` describes
  `LocalWorkspace` as direct local filesystem and command execution. Its
  `execute_command` calls the local command utility with the workspace as
  `cwd`.
- `openhands-tools/openhands/tools/terminal/definition.py` obtains
  `working_dir` from `conv_state.workspace` and constructs
  `TerminalExecutor` in the Agent Server process.
- `openhands-tools/openhands/tools/file_editor/definition.py` constructs
  `FileEditorExecutor` with the same local workspace root.
- the terminal subprocess and tmux implementations call
  `build_terminal_env`, which starts with a copy of the Agent Server process
  environment.

Therefore `LocalWorkspace` is not a sandbox. Terminal and File Editor are
bounded only when the Agent Server process itself is the bounded disposable
Attempt container.

## Environment inheritance

`openhands-sdk/openhands/sdk/utils/command.py` at the pinned commit removes
only the exact `SESSION_API_KEY` name from child-process environments. It does
not remove `LLM_API_KEY`, `LITELLM_MASTER_KEY`, `OH_SESSION_API_KEYS_0`, or
provider-key names. Any of those names placed in the Agent Server environment
can be inherited by Terminal.

The successor design consequently:

- uses the legacy upstream-supported `SESSION_API_KEY` name for the
  disposable Agent Server session credential so the pinned sanitizer removes
  it from tool subprocesses;
- supplies no provider key or LiteLLM master key to the Attempt container;
- supplies model execution authority as a bounded LiteLLM virtual key through
  the trusted conversation request, not the container environment.

## Independent Attempt-container support

The selected image declares the non-root `openhands` user and the fixed
`tini -- /usr/local/bin/openhands-agent-server` entrypoint. The upstream
Docker example runs that Agent Server as a remote workspace container. The
minimal image does not require a Docker socket for local Terminal or File
Editor execution.

The fixed image can therefore be launched once per Attempt with one workspace
bind, a private internal executor network, dropped capabilities,
`no-new-privileges`, bounded CPU/memory/PIDs, a read-only root filesystem, and
explicit tmpfs mounts. Docker authority remains outside that container.

## Unsafe starting-head observation

The exact starting head
`ccbafe1a4b3119d20dd1995d5cfb7d230c66bd50` was inspected by exact-name
presence only:

```text
current_agent_server_docker_socket = PRESENT
current_terminal_LLM_API_KEY = PRESENT
current_terminal_LITELLM_MASTER_KEY = PRESENT
current_terminal_provider_key = ABSENT
```

No value, prefix, hash, header, environment dump, or `/proc/*/environ` content
was collected. These booleans record the unsafe predecessor state; they are
not successor acceptance evidence.
