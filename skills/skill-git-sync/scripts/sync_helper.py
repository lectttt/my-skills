#!/usr/bin/env python3
import os
import subprocess
import argparse
from pathlib import Path

HOME = Path.home()
AGENTS_SKILLS = HOME / ".agents" / "skills"
REPO_ROOT = HOME / ".anyskill" / "repo"

def run_git(repo_path, args):
    try:
        cmd = ["git", "-C", str(repo_path)] + args
        # Add timeout to prevent hanging on credential prompts or network issues
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        print(f"Error: Git command timed out in {repo_path}")
        return None
    except subprocess.CalledProcessError as e:
        # Standardize error output for diagnosis
        return f"ERROR: {e.stderr.strip()}"

def find_repo_for_skill(skill_name):
    # Standard check: is it in our main repo?
    skill_in_repo = REPO_ROOT / "skills" / skill_name
    if skill_in_repo.exists():
        return REPO_ROOT
    
    # Alternative check: is the skill dir itself a git repo?
    skill_path = AGENTS_SKILLS / skill_name
    if (skill_path / ".git").exists():
        return skill_path
    
    # Resolve symlink to see where it points
    if skill_path.is_symlink():
        resolved = skill_path.resolve()
        # Traverse up to find .git
        curr = resolved
        while curr != HOME and curr != curr.parent:
            if (curr / ".git").exists():
                return curr
            curr = curr.parent
            
    return None

def cmd_status(args):
    print(f"{'Skill':<25} | {'Repo Path':<40} | {'Status'}")
    print("-" * 80)
    if not AGENTS_SKILLS.exists():
        print("No skills found in ~/.agents/skills")
        return

    for item in AGENTS_SKILLS.iterdir():
        if item.is_dir() or item.is_symlink():
            repo = find_repo_for_skill(item.name)
            if repo:
                status = run_git(repo, ["status", "--short"])
                status_str = "Dirty (changes pending)" if status else "Clean"
                print(f"{item.name:<25} | {str(repo).replace(str(HOME), '~'):<40} | {status_str}")
            else:
                print(f"{item.name:<25} | {'No Git Repo Found':<40} | -")

def cmd_push(args):
    target_skills = []
    if args.all:
        for item in AGENTS_SKILLS.iterdir():
            if item.is_dir() or item.is_symlink():
                target_skills.append(item.name)
    else:
        target_skills = [args.skill]

    repos_to_push = set()
    for name in target_skills:
        repo = find_repo_for_skill(name)
        if repo:
            repos_to_push.add(repo)
        else:
            print(f"Warning: No repo found for skill '{name}'")

    if not repos_to_push:
        print("Nothing to push.")
        return

    for repo in repos_to_push:
        print(f"\n--- Syncing Repo: {repo} ---")
        
        # 1. Pull changes first to avoid conflicts
        print("Checking for remote updates...")
        pull_res = run_git(repo, ["pull", "--rebase", "origin", "main"])
        if pull_res and "ERROR" in pull_res:
             if "unstaged changes" in pull_res or "locally modified files" in pull_res:
                 print("Local changes detected. Stashing before pull...")
                 run_git(repo, ["stash"])
                 run_git(repo, ["pull", "--rebase", "origin", "main"])
                 run_git(repo, ["stash", "pop"])
             else:
                 print(f"Warning: Pull failed. Proceeding with caution. Details: {pull_res}")

        # 2. Check status
        status = run_git(repo, ["status", "--short"])
        if not status or status.startswith("ERROR"):
            print("No local changes to commit. Syncing metadata (push)...")
            run_git(repo, ["push", "origin", "main"])
            continue
            
        print("Pending changes:")
        print(status)
        
        # 3. Add, Commit, Push
        run_git(repo, ["add", "."])
        commit_msg = args.message if args.message else "chore: sync skill updates"
        run_git(repo, ["commit", "-m", commit_msg])
        
        print("Pushing to GitHub...")
        push_res = run_git(repo, ["push", "origin", "main"])
        if push_res and "ERROR" in push_res:
            print(f"Failed to push: {push_res}")
        else:
            print("Success!")

def main():
    parser = argparse.ArgumentParser(description="Skill Git Sync Helper")
    subparsers = parser.add_subparsers(dest="command")

    # Status
    subparsers.add_parser("status", help="Check git status of all skills")

    # Push
    push_parser = subparsers.add_parser("push", help="Push changes to cloud")
    push_parser.add_argument("skill", nargs="?", help="Skill name to push")
    push_parser.add_argument("--all", "-a", action="store_true", help="Push all skills")
    push_parser.add_argument("--message", "-m", help="Commit message")

    args = parser.parse_args()

    if args.command == "status":
        cmd_status(args)
    elif args.command == "push":
        if not args.skill and not args.all:
            print("Please specify a skill name or use --all")
            return
        cmd_push(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
