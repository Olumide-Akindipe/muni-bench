#!/usr/bin/env python3
"""Create a GitHub repository, push the project, and optionally tag a release.

Runs publish_gate.py first and stops if it fails. Reads the token from the
GITHUB_TOKEN environment variable only; never pass tokens as arguments and never
write them to files.

Token scopes: fine-grained token with "Administration: write" (to create) and
"Contents: write" (to push), or a classic token with "repo".

Usage:
  export GITHUB_TOKEN=...            # set in the shell, not in any file
  python publish_github.py <project_dir> --repo <name> [--description "..."]
                           [--private] [--release v0.1.0] [--release-notes "..."]
                           [--dry-run] [--skip-gate]
"""

import argparse
import os
import subprocess
import sys

import requests

API = "https://api.github.com"
HERE = os.path.dirname(os.path.abspath(__file__))


def sh(cmd, cwd, check=True):
    print("  $", " ".join(cmd))
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)


def headers(token):
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "open-project-build"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project_dir")
    ap.add_argument("--repo", required=True, help="repository name to create")
    ap.add_argument("--description", default="")
    ap.add_argument("--private", action="store_true")
    ap.add_argument("--release", help="tag to create, e.g. v0.1.0")
    ap.add_argument("--release-notes", default="")
    ap.add_argument("--dry-run", action="store_true", help="show what would happen; no network writes")
    ap.add_argument("--skip-gate", action="store_true", help="only for planning-directory pushes; never for publications")
    a = ap.parse_args()

    root = os.path.abspath(a.project_dir)
    if not a.skip_gate:
        gate = subprocess.run([sys.executable, os.path.join(HERE, "publish_gate.py"), root])
        if gate.returncode != 0:
            sys.exit("gate failed; not publishing")

    token = os.environ.get("GITHUB_TOKEN")
    if not token and not a.dry_run:
        sys.exit("GITHUB_TOKEN is not set. Export it in the shell (never write it to a file).")

    if a.dry_run:
        print(f"[dry-run] would create repo '{a.repo}' (private={a.private}), push {root}, "
              f"release={a.release or 'none'}")
        return

    # who am I
    me = requests.get(f"{API}/user", headers=headers(token), timeout=30)
    me.raise_for_status()
    owner = me.json()["login"]

    # create repo (idempotent: 422 means it exists)
    r = requests.post(f"{API}/user/repos", headers=headers(token), timeout=30, json={
        "name": a.repo, "description": a.description, "private": a.private, "auto_init": False})
    if r.status_code == 201:
        print(f"created https://github.com/{owner}/{a.repo}")
    elif r.status_code == 422:
        print(f"repository {owner}/{a.repo} already exists; pushing to it")
    else:
        r.raise_for_status()

    # git init/commit/push using the token only in the remote URL for this push
    if not os.path.isdir(os.path.join(root, ".git")):
        sh(["git", "init", "-b", "main"], root)
    sh(["git", "add", "-A"], root)
    status = sh(["git", "status", "--porcelain"], root).stdout
    if status.strip():
        # commit identity from AUTHORS.json (first author) so the history carries the author's name
        name, email = "open-project-build", "noreply@example.invalid"
        authors_path = os.path.join(root, "AUTHORS.json")
        if os.path.isfile(authors_path):
            import json
            try:
                first = json.load(open(authors_path))["authors"][0]
                name = first.get("name") or name
                email = first.get("email") or email
            except (KeyError, IndexError, ValueError):
                pass
        sh(["git", "-c", f"user.name={name}", "-c", f"user.email={email}",
            "commit", "-m", "Publish"], root)
    remote = f"https://x-access-token:{token}@github.com/{owner}/{a.repo}.git"
    sh(["git", "remote", "remove", "origin"], root, check=False)
    sh(["git", "remote", "add", "origin", remote], root)
    sh(["git", "push", "-u", "origin", "main"], root)
    # scrub the token from the stored remote
    sh(["git", "remote", "set-url", "origin", f"https://github.com/{owner}/{a.repo}.git"], root)
    print(f"pushed to https://github.com/{owner}/{a.repo}")

    if a.release:
        rel = requests.post(f"{API}/repos/{owner}/{a.repo}/releases", headers=headers(token), timeout=30,
                            json={"tag_name": a.release, "name": a.release,
                                  "body": a.release_notes, "target_commitish": "main"})
        rel.raise_for_status()
        print(f"release {a.release}: {rel.json().get('html_url')}")
        print("If the Zenodo-GitHub integration is enabled for this repo, a DOI will mint automatically.")


if __name__ == "__main__":
    main()
