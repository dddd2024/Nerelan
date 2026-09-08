use serde::Serialize;
use std::net::{SocketAddr, TcpStream};
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::Duration;

const FRONTEND_PORT: u16 = 4173;
const FRONTEND_HOST: &str = "127.0.0.1";

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct RuntimeStatus {
    running: bool,
    frontend_reachable: bool,
    frontend_port: u16,
    repo_root: Option<String>,
    error: Option<String>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct RuntimeStartResult {
    started: bool,
    pid: Option<u32>,
    repo_root: Option<String>,
    error: Option<String>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct RuntimeStopResult {
    stopped: bool,
    error: Option<String>,
}

fn resolve_repo_root() -> Option<PathBuf> {
    if let Ok(exe) = std::env::current_exe() {
        let mut dir = exe.parent().map(Path::to_path_buf)?;
        loop {
            if dir.join("dev-up.ps1").is_file() {
                return Some(dir);
            }
            if !dir.pop() {
                break;
            }
        }
    }
    let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let repo = manifest_dir
        .parent()
        .and_then(Path::parent)
        .map(Path::to_path_buf);
    if let Some(ref repo) = repo {
        if repo.join("dev-up.ps1").is_file() {
            return Some(repo.clone());
        }
    }
    None
}

fn frontend_reachable() -> bool {
    let addr: SocketAddr = match format!("{FRONTEND_HOST}:{FRONTEND_PORT}").parse() {
        Ok(addr) => addr,
        Err(_) => return false,
    };
    TcpStream::connect_timeout(&addr, Duration::from_millis(500)).is_ok()
}

#[tauri::command]
fn runtime_status() -> RuntimeStatus {
    let repo_root = resolve_repo_root();
    let reachable = frontend_reachable();
    RuntimeStatus {
        running: reachable,
        frontend_reachable: reachable,
        frontend_port: FRONTEND_PORT,
        repo_root: repo_root.clone().map(|p| p.display().to_string()),
        error: if repo_root.is_none() {
            Some("repository root could not be resolved from backend context".to_string())
        } else {
            None
        },
    }
}

#[tauri::command]
fn start_runtime() -> RuntimeStartResult {
    let Some(repo_root) = resolve_repo_root() else {
        return RuntimeStartResult {
            started: false,
            pid: None,
            repo_root: None,
            error: Some("repository root could not be resolved from backend context".to_string()),
        };
    };
    let script = repo_root.join("dev-up.ps1");
    if !script.is_file() {
        return RuntimeStartResult {
            started: false,
            pid: None,
            repo_root: Some(repo_root.display().to_string()),
            error: Some(format!("dev-up.ps1 not found at {}", script.display())),
        };
    }
    let child = Command::new("powershell.exe")
        .arg("-NoProfile")
        .arg("-NonInteractive")
        .arg("-NoLogo")
        .arg("-ExecutionPolicy")
        .arg("Bypass")
        .arg("-File")
        .arg(&script)
        .arg("-NoBrowser")
        .arg("-RepoDir")
        .arg(&repo_root)
        .spawn();
    match child {
        Ok(child) => RuntimeStartResult {
            started: true,
            pid: Some(child.id()),
            repo_root: Some(repo_root.display().to_string()),
            error: None,
        },
        Err(err) => RuntimeStartResult {
            started: false,
            pid: None,
            repo_root: Some(repo_root.display().to_string()),
            error: Some(format!("failed to launch dev-up.ps1: {err}")),
        },
    }
}

#[tauri::command]
fn stop_runtime() -> RuntimeStopResult {
    let Some(repo_root) = resolve_repo_root() else {
        return RuntimeStopResult {
            stopped: false,
            error: Some("repository root could not be resolved from backend context".to_string()),
        };
    };
    let script = repo_root.join("dev-down.ps1");
    if !script.is_file() {
        return RuntimeStopResult {
            stopped: false,
            error: Some(format!("dev-down.ps1 not found at {}", script.display())),
        };
    }
    let child = Command::new("powershell.exe")
        .arg("-NoProfile")
        .arg("-NonInteractive")
        .arg("-NoLogo")
        .arg("-ExecutionPolicy")
        .arg("Bypass")
        .arg("-File")
        .arg(&script)
        .arg("-RepoDir")
        .arg(&repo_root)
        .spawn();
    match child {
        Ok(_) => RuntimeStopResult {
            stopped: true,
            error: None,
        },
        Err(err) => RuntimeStopResult {
            stopped: false,
            error: Some(format!("failed to launch dev-down.ps1: {err}")),
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
        .setup(|_app| {
            let _ = start_runtime();
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
