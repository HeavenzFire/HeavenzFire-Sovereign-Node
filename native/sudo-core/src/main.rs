use std::env;
use std::process::ExitCode;

#[derive(Debug, PartialEq, Eq)]
enum Decision {
    Allow(&'static str),
    Deny(&'static str),
}

fn evaluate(capability: &str, resource: &str) -> Decision {
    match capability {
        "workspace-read" | "workspace-write" => {
            if resource.is_empty()
                || resource.starts_with('/')
                || resource.contains(char::from(92))
                || resource.split('/').any(|part| part == ".." || part.is_empty())
            {
                return Decision::Deny("resource must be a relative workspace path without traversal");
            }
            if resource.split('/').any(|part| {
                part.eq_ignore_ascii_case(".git")
                    || part.eq_ignore_ascii_case(".env")
                    || part.eq_ignore_ascii_case("secrets")
            }) {
                return Decision::Deny("sensitive workspace path is protected by default");
            }
            Decision::Allow("policy check passed; no operation was executed")
        }
        "bind-port" => match resource.parse::<u16>() {
            Ok(port) if port >= 1024 => {
                Decision::Allow("unprivileged port passes policy; no socket was opened")
            }
            Ok(_) => Decision::Deny("ports below 1024 require a separate OS-enforced capability grant"),
            Err(_) => Decision::Deny("port must be an integer from 1 to 65535"),
        },
        "network-fetch" => Decision::Deny("network access is disabled in this MVP"),
        "privileged-exec" => Decision::Deny("arbitrary privileged execution is never permitted"),
        _ => Decision::Deny("unknown capability; default-deny policy"),
    }
}

fn main() -> ExitCode {
    let args: Vec<String> = env::args().skip(1).collect();
    if args.len() != 3 || args[0] != "check" {
        eprintln!("Usage: sudo-core-policy check <capability> <resource>");
        eprintln!("Policy-only MVP: no commands are executed and no files or sockets are accessed.");
        return ExitCode::from(2);
    }

    match evaluate(&args[1], &args[2]) {
        Decision::Allow(reason) => {
            println!("DECISION=ALLOW");
            println!("REASON={reason}");
            ExitCode::SUCCESS
        }
        Decision::Deny(reason) => {
            println!("DECISION=DENY");
            println!("REASON={reason}");
            ExitCode::from(1)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::{evaluate, Decision};

    #[test]
    fn permits_relative_workspace_path() {
        assert!(matches!(evaluate("workspace-read", "src/main.rs"), Decision::Allow(_)));
    }

    #[test]
    fn rejects_parent_traversal() {
        assert!(matches!(evaluate("workspace-write", "../outside.txt"), Decision::Deny(_)));
    }

    #[test]
    fn rejects_sensitive_paths() {
        assert!(matches!(evaluate("workspace-read", ".env"), Decision::Deny(_)));
        assert!(matches!(evaluate("workspace-read", ".git/config"), Decision::Deny(_)));
    }

    #[test]
    fn allows_unprivileged_port_without_opening_socket() {
        assert!(matches!(evaluate("bind-port", "8080"), Decision::Allow(_)));
    }

    #[test]
    fn denies_privileged_ports_and_arbitrary_execution() {
        assert!(matches!(evaluate("bind-port", "80"), Decision::Deny(_)));
        assert!(matches!(evaluate("privileged-exec", "powershell"), Decision::Deny(_)));
    }

    #[test]
    fn denies_network_by_default() {
        assert!(matches!(evaluate("network-fetch", "https://example.com"), Decision::Deny(_)));
    }

    #[test]
    fn rejects_invalid_ports() {
        assert!(matches!(evaluate("bind-port", "not-a-port"), Decision::Deny(_)));
        assert!(matches!(evaluate("bind-port", "70000"), Decision::Deny(_)));
    }
}
