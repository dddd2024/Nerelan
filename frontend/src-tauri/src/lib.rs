// Nerelan desktop shell — Tauri 2 native startup bridge.
//
// This slice reuses the existing React/Vite frontend inside the native
// WebView and owns the runtime bootstrap from the backend context:
//   * repository/runtime paths are resolved from the backend (the compiled
//     artifact location), never from the caller's working directory;
//   * the existing dev-up.ps1 lifecycle is invoked through discrete
//     PowerShell arguments (explicit executable + -NoProfile +
//     -ExecutionPolicy Bypass + -File + script path + -NoBrowser), never by
//     concatenating a quoted command-line string;
//   * no generic shell/command bridge is exposed to WebView JavaScript; the
//     only IPC surface is a narrow set of fixed runtime commands.

use serde::Serialize;
use std::net::TcpStream;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::Duration;

const FRONTEND_URL: &str = "http://127.0.0.1:4173";
const FRONTEND_HOST: &str = "127.0.0.1";
const FRONTEND_PORT: u16 = 4173;

/// Resolve the repository root from backend context.
///
/// Walks upward from the compiled artifact's parent directory until it finds
/// the repository-owned `dev-up.ps1` marker. Falls back to the compile-time
/// backend context (`CARGO_MANIFEST_DIR` = `frontend/src-tauri`) if the
/// runtime artifact is not inside the repository tree. It never consults the
/// caller's current working directory.
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
  let repo_from_manifest = manifest_dir
    .parent()
    .and_then(Path::parent)
    .map(Path::to_path_buf);
  if let Some(repo) = repo_from_manifest {
    if repo.join("dev-up.ps1").is_file() {
      return Some(repo);
    }
  }
  None
}

fn is_frontend_reachable() -> bool {
  let addr: std::net::SocketAddr = match format!("{FRONTEND_HOST}:{FRONTEND_PORT}").parse() {
    Ok(addr) => addr,
    Err(_) => return false,
  };
  TcpStream::connect_timeout(&addr, Duration::from_millis(500)).is_ok()
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct RuntimeStatus {
  running: bool,
  frontend_reachable: bool,
  frontend_url: &'static str,
  repo_root: Option<String>,
  error: Option<String>,
}

/// Read-only runtime status command for the WebView. Performs no mutation and
/// accepts no arbitrary arguments.
#[tauri::command]
fn runtime_status() -> RuntimeStatus {
  let repo_root = resolve_repo_root();
  let error = if repo_root.is_none() {
    Some("repository root could not be resolved from backend context".to_string())
  } else {
    None
  };
  RuntimeStatus {
    running: is_frontend_reachable(),
    frontend_reachable: is_frontend_reachable(),
    frontend_url: FRONTEND_URL,
    repo_root: repo_root.map(|p| p.display().to_string()),
    error,
  }
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct RuntimeStartResult {
  started: bool,
  pid: Option<u32>,
  repo_root: Option<String>,
  error: Option<String>,
}

/// Start (or reconnect to) the existing local runtime by invoking the
/// repository-owned `dev-up.ps1` lifecycle with discrete PowerShell
/// arguments. No command string is concatenated. Accepts no WebView input.
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
  // Discrete argument boundaries: explicit executable, -NoProfile,
  // -ExecutionPolicy Bypass, -File, the exact script path, and the -NoBrowser
  // switch so the desktop shell does not open a separate external browser.
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

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct RuntimeStopResult {
  stopped: bool,
  error: Option<String>,
}

/// Stop the runtime children recorded by `dev-up.ps1` using `dev-down.ps1`
/// with discrete PowerShell arguments. Accepts no WebView input.
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
      // The backend owns runtime bootstrap. Reconnect to the existing local
      // runtime (dev-up is idempotent) without opening an external browser.
      let _ = start_runtime();
      Ok(())
    })
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
