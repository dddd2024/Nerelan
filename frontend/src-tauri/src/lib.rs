use serde::Serialize;
use std::io::{Read, Write};
use std::net::{SocketAddr, TcpStream};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::thread;
use std::time::Duration;

const LOOPBACK: &str = "127.0.0.1";
const FRONTEND_PORT: u16 = 4173;
const TASK_API_PORT: u16 = 8766;
const MODEL_CONTROL_PORT: u16 = 8765;

const FRONTEND_URL: &str = "http://127.0.0.1:4173";
const TASK_API_URL: &str = "http://127.0.0.1:8766";
const MODEL_CONTROL_URL: &str = "http://127.0.0.1:8765";

const FRONTEND_PROBE_PATH: &str = "/";
const TASK_API_PROBE_PATH: &str = "/api/tasks";
const MODEL_CONTROL_PROBE_PATH: &str = "/api/model-profiles";

const START_TIMEOUT: Duration = Duration::from_secs(300);
const STOP_TIMEOUT: Duration = Duration::from_secs(180);
const PROBE_TIMEOUT: Duration = Duration::from_millis(1500);
const POLL_INTERVAL: Duration = Duration::from_millis(250);
const OUTPUT_CAP: usize = 64 * 1024;
const DETAIL_CAP: usize = 1800;

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct EndpointState {
    reachable: bool,
    url: &'static str,
    host: &'static str,
    port: u16,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct RuntimeStatus {
    ready: bool,
    frontend: EndpointState,
    task_api: EndpointState,
    model_control: EndpointState,
    repo_root: Option<String>,
    error: Option<String>,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct RuntimeStartResult {
    started: bool,
    repo_root: Option<String>,
    error: Option<String>,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct RuntimeStopResult {
    stopped: bool,
    repo_root: Option<String>,
    error: Option<String>,
}

#[derive(Debug, Clone)]
struct ScriptOutcome {
    exit_code: Option<i32>,
    timed_out: bool,
    stdout: Vec<u8>,
    stderr: Vec<u8>,
}

fn manifest_dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

fn resolve_repo_root() -> Option<PathBuf> {
    let mut candidate = std::env::current_exe()
        .ok()
        .and_then(|path| path.parent().map(Path::to_path_buf));
    while let Some(mut dir) = candidate.take() {
        if dir.join("dev-up.ps1").is_file() && dir.join("dev-down.ps1").is_file() {
            return Some(dir);
        }
        if !dir.pop() {
            break;
        }
    }
    let from_manifest = manifest_dir()
        .parent()
        .and_then(Path::parent)
        .map(Path::to_path_buf);
    if let Some(dir) = from_manifest {
        if dir.join("dev-up.ps1").is_file() && dir.join("dev-down.ps1").is_file() {
            return Some(dir);
        }
    }
    None
}

fn http_status(host: &str, port: u16, path: &str) -> Option<String> {
    let addr: SocketAddr = match format!("{host}:{port}").parse() {
        Ok(value) => value,
        Err(_) => return None,
    };
    let mut stream = match TcpStream::connect_timeout(&addr, PROBE_TIMEOUT) {
        Ok(stream) => stream,
        Err(_) => return None,
    };
    if stream.set_read_timeout(Some(PROBE_TIMEOUT)).is_err() {
        return None;
    }
    if stream.set_write_timeout(Some(PROBE_TIMEOUT)).is_err() {
        return None;
    }
    let request = format!(
        "GET {path} HTTP/1.1\r\nHost: {host}:{port}\r\nConnection: close\r\nAccept: */*\r\nUser-Agent: nerelan-desktop\r\n\r\n"
    );
    if stream.write_all(request.as_bytes()).is_err() {
        return None;
    }
    let mut buffer: Vec<u8> = Vec::with_capacity(1024);
    let mut chunk = [0u8; 512];
    loop {
        if buffer.windows(4).any(|window| window == b"\r\n\r\n") {
            break;
        }
        match stream.read(&mut chunk) {
            Ok(0) => break,
            Ok(read) => buffer.extend_from_slice(&chunk[..read]),
            Err(_) => break,
        }
        if buffer.len() > 8192 {
            break;
        }
    }
    let head = String::from_utf8_lossy(&buffer);
    let first_line = head.lines().next()?;
    let columns: Vec<&str> = first_line.split_whitespace().collect();
    if columns.len() < 2 {
        return None;
    }
    Some(columns[1].to_string())
}

fn probe_endpoint(host: &'static str, port: u16, path: &str, url: &'static str) -> EndpointState {
    EndpointState {
        reachable: http_status(host, port, path).is_some(),
        url,
        host,
        port,
    }
}

fn drain_bounded<R: Read + Send + 'static>(mut reader: R) -> Vec<u8> {
    let mut collected = Vec::new();
    let mut chunk = [0u8; 4096];
    loop {
        if collected.len() >= OUTPUT_CAP {
            break;
        }
        match reader.read(&mut chunk) {
            Ok(0) => break,
            Ok(read) => {
                let take = read.min(OUTPUT_CAP - collected.len());
                collected.extend_from_slice(&chunk[..take]);
            }
            Err(_) => break,
        }
    }
    collected
}

fn spawn_drainer<T: Read + Send + 'static>(stream: Option<T>) -> Option<thread::JoinHandle<Vec<u8>>> {
    stream.map(|handle| thread::spawn(move || drain_bounded(handle)))
}

fn run_lifecycle_script(
    script: &Path,
    repo_root: &Path,
    timeout: Duration,
) -> std::io::Result<ScriptOutcome> {
    let mut command = Command::new("powershell.exe");
    command
        .arg("-NoProfile")
        .arg("-NonInteractive")
        .arg("-NoLogo")
        .arg("-ExecutionPolicy")
        .arg("Bypass")
        .arg("-File")
        .arg(script)
        .arg("-NoBrowser")
        .arg("-RepoDir")
        .arg(repo_root)
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());

    let mut child = command.spawn()?;
    let stdout_handle = spawn_drainer(child.stdout.take());
    let stderr_handle = spawn_drainer(child.stderr.take());

    let deadline = std::time::Instant::now() + timeout;
    let mut exit_code: Option<i32> = None;
    let mut timed_out = false;
    loop {
        match child.try_wait()? {
            Some(status) => {
                exit_code = status.code();
                break;
            }
            None => {
                if std::time::Instant::now() >= deadline {
                    timed_out = true;
                    let _ = child.kill();
                    let _ = child.wait();
                    break;
                }
                thread::sleep(POLL_INTERVAL);
            }
        }
    }

    let stdout = stdout_handle
        .map(|handle| handle.join().unwrap_or_default())
        .unwrap_or_default();
    let stderr = stderr_handle
        .map(|handle| handle.join().unwrap_or_default())
        .unwrap_or_default();

    Ok(ScriptOutcome {
        exit_code,
        timed_out,
        stdout,
        stderr,
    })
}

fn sanitize_output(bytes: &[u8], cap: usize) -> String {
    let flattened: String = String::from_utf8_lossy(bytes)
        .chars()
        .map(|character| if character.is_control() { ' ' } else { character })
        .collect();
    let characters: Vec<char> = flattened.chars().collect();
    let start = characters.len().saturating_sub(cap);
    characters[start..].iter().collect()
}

fn sanitized_detail(outcome: &ScriptOutcome) -> String {
    let stderr_tail = sanitize_output(&outcome.stderr, DETAIL_CAP / 2);
    let stdout_tail = sanitize_output(&outcome.stdout, DETAIL_CAP / 2);
    let mut detail = String::new();
    if outcome.timed_out {
        detail.push_str("timed out before the script exited");
    }
    if let Some(code) = outcome.exit_code {
        if !detail.is_empty() {
            detail.push_str("; ");
        }
        detail.push_str(&format!("exit_code={code}"));
    }
    if !stderr_tail.is_empty() {
        if !detail.is_empty() {
            detail.push_str("; stderr=");
        }
        detail.push_str(&stderr_tail);
    }
    if detail.is_empty() && !stdout_tail.is_empty() {
        detail.push_str(&stdout_tail);
    }
    if detail.is_empty() {
        detail.push_str("script produced no diagnostic output");
    }
    detail.chars().take(DETAIL_CAP).collect()
}

#[tauri::command]
fn runtime_status() -> RuntimeStatus {
    let repo_root = resolve_repo_root();
    let frontend = probe_endpoint(LOOPBACK, FRONTEND_PORT, FRONTEND_PROBE_PATH, FRONTEND_URL);
    let task_api = probe_endpoint(LOOPBACK, TASK_API_PORT, TASK_API_PROBE_PATH, TASK_API_URL);
    let model_control =
        probe_endpoint(LOOPBACK, MODEL_CONTROL_PORT, MODEL_CONTROL_PROBE_PATH, MODEL_CONTROL_URL);
    let ready = frontend.reachable && task_api.reachable && model_control.reachable;

    let mut problems: Vec<&str> = Vec::new();
    if repo_root.is_none() {
        problems.push("repository root unresolved");
    }
    if !frontend.reachable {
        problems.push("frontend");
    }
    if !task_api.reachable {
        problems.push("task_api");
    }
    if !model_control.reachable {
        problems.push("model_control");
    }

    RuntimeStatus {
        ready,
        frontend,
        task_api,
        model_control,
        repo_root: repo_root.map(|path| path.display().to_string()),
        error: if problems.is_empty() {
            None
        } else {
            Some(format!("runtime not ready: {}", problems.join(", ")))
        },
    }
}

#[tauri::command]
fn start_runtime() -> RuntimeStartResult {
    let repo_root = match resolve_repo_root() {
        Some(root) => root,
        None => {
            return RuntimeStartResult {
                started: false,
                repo_root: None,
                error: Some(
                    "repository root could not be resolved from backend context".to_string(),
                ),
            }
        }
    };
    let display = repo_root.display().to_string();
    let script = repo_root.join("dev-up.ps1");
    if !script.is_file() {
        return RuntimeStartResult {
            started: false,
            repo_root: Some(display),
            error: Some(format!("dev-up.ps1 not found at {}", script.display())),
        };
    }

    match run_lifecycle_script(&script, &repo_root, START_TIMEOUT) {
        Ok(outcome) if !outcome.timed_out && outcome.exit_code == Some(0) => RuntimeStartResult {
            started: true,
            repo_root: Some(display),
            error: None,
        },
        Ok(outcome) => RuntimeStartResult {
            started: false,
            repo_root: Some(display),
            error: Some(sanitized_detail(&outcome)),
        },
        Err(io_error) => RuntimeStartResult {
            started: false,
            repo_root: Some(display),
            error: Some(format!(
                "failed to launch powershell.exe for dev-up.ps1: {io_error}"
            )),
        },
    }
}

#[tauri::command]
fn stop_runtime() -> RuntimeStopResult {
    let repo_root = match resolve_repo_root() {
        Some(root) => root,
        None => {
            return RuntimeStopResult {
                stopped: false,
                repo_root: None,
                error: Some(
                    "repository root could not be resolved from backend context".to_string(),
                ),
            }
        }
    };
    let display = repo_root.display().to_string();
    let script = repo_root.join("dev-down.ps1");
    if !script.is_file() {
        return RuntimeStopResult {
            stopped: false,
            repo_root: Some(display),
            error: Some(format!("dev-down.ps1 not found at {}", script.display())),
        };
    }

    match run_lifecycle_script(&script, &repo_root, STOP_TIMEOUT) {
        Ok(outcome) if !outcome.timed_out && outcome.exit_code == Some(0) => RuntimeStopResult {
            stopped: true,
            repo_root: Some(display),
            error: None,
        },
        Ok(outcome) => RuntimeStopResult {
            stopped: false,
            repo_root: Some(display),
            error: Some(sanitized_detail(&outcome)),
        },
        Err(io_error) => RuntimeStopResult {
            stopped: false,
            repo_root: Some(display),
            error: Some(format!(
                "failed to launch powershell.exe for dev-down.ps1: {io_error}"
            )),
        },
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            runtime_status,
            start_runtime,
            stop_runtime
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
