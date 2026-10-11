"""Read current main with existing HTTPS Git authentication; keep private source ignored."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".local"
CORE = LOCAL / "core-brain"
REMOTE = "https://github.com/sangkeat/LifeOS-Foundry.git"
SOURCE_FILES = [
    "A00_SYSTEM_INDEX.md", "A01_RUNTIME_GATES.md", "A02_OPERATING_CONTEXT.md",
    "A03_CONTEXT_ROUTER.md", "AGENTS.md", "PROJECT_CANON.md",
    "protocols/lifeos-command-registry.md", "skills/lifeos-work-flow/SKILL.md",
    "protocols/holographic-memory.md", "protocols/cloud-portable-active-recall.md",
    "tools/agent-process-monitor/server.py", "tools/agent-process-monitor/dashboard.html",
    "tools/agent-process-monitor/owner-status.js", "tools/agent-process-monitor/workflow.json",
    "runtime/status/goal-registry.json", "runtime/status/mission-state.json", "runtime/status/session-plan.json",
]


def git(*args, cwd=None):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True, timeout=90).strip()


def main():
    LOCAL.mkdir(exist_ok=True)
    if CORE.exists():
        if CORE.is_symlink() or not (CORE / ".git").is_dir():
            raise SystemExit("Existing source directory is not the managed checkout; preserved.")
        if git("remote", "get-url", "origin", cwd=CORE) != REMOTE:
            raise SystemExit("Unexpected source identity; preserved.")
        if git("status", "--porcelain", "--untracked-files=all", cwd=CORE):
            raise SystemExit("Core Brain has local changes; preserved. Resolve separately before refreshing.")
        git("fetch", "--depth", "1", "origin", "main", cwd=CORE)
        git("-c", "advice.detachedHead=false", "checkout", "--detach", "FETCH_HEAD", cwd=CORE)
    else:
        git("clone", "--depth", "1", "--branch", "main", REMOTE, str(CORE))
    revision = git("rev-parse", "--verify", "HEAD^{commit}", cwd=CORE)
    tip = git("ls-remote", "origin", "refs/heads/main", cwd=CORE).split()
    if len(tip) != 2 or tip[0] != revision:
        raise SystemExit("Source moved during retrieval. Rerun bootstrap before using this snapshot.")
    fingerprints = {name: hashlib.sha256((CORE / name).read_bytes()).hexdigest() for name in SOURCE_FILES}
    observed = datetime.now(timezone.utc).isoformat()
    manifest = {"repository": "sangkeat/LifeOS-Foundry", "branch": "main", "revision": revision,
                "observed_at": observed, "files": fingerprints, "authority": "source pointers, not Canon"}
    # Preserve record timestamps. Fetch time must not rejuvenate runtime snapshots.
    snapshots = LOCAL / "snapshots"
    snapshots.mkdir(exist_ok=True)
    for name in ["goal-registry.json", "mission-state.json", "session-plan.json"]:
        src = CORE / "runtime/status" / name
        staged = snapshots / (name + ".tmp")
        staged.write_bytes(src.read_bytes())
        staged.replace(snapshots / name)
    # Publish provenance last. Interrupted refresh cannot validate mixed snapshots.
    staged_manifest = LOCAL / "source.json.tmp"
    staged_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    staged_manifest.replace(LOCAL / "source.json")
    print(f"Current Core Brain read verified: {revision}")
    print("Private source/snapshots stay under ignored .local; no secret requirement.")


if __name__ == "__main__":
    main()
