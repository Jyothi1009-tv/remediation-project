import os
import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, check=True):
    print(f"\n>>> Running: {cmd}")
    result = subprocess.run(cmd, shell=True, text=True)
    if check and result.returncode != 0:
        print(f"Command failed: {cmd}")
        sys.exit(result.returncode)
    return result

def get_env(var, default=None):
    value = os.environ.get(var, default)
    if value is None:
        print(f"Missing required environment variable: {var}")
        sys.exit(1)
    return value

def main():
    print("=== OSS Upgrade Agent Started ===")

    # Environment variables from GitHub Actions
    base_branch = get_env("GITHUB_REF_NAME")
    github_token = get_env("GITHUB_TOKEN")

    # Step 1: Generate branch name
    commit_id = subprocess.check_output("git rev-parse --short HEAD", shell=True).decode().strip()
    branch_name = f"feature/{base_branch}-{commit_id}"

    # Step 2: Git config
    run_cmd('git config --global user.email "agent@automation.com"')
    run_cmd('git config --global user.name "OSS agent"')

    # Step 3: Create feature branch
    run_cmd(f"git checkout -b {branch_name}")

    # Step 4: Build project
    run_cmd("mvn clean install")

    # Step 5: Run OWASP dependency check
    run_cmd("mvn verify org.owasp:dependency-check-maven:check")

    # Step 6: Collect reports
    reports_dir = Path("reports/owasp")
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Find and move reports
    run_cmd(f"find . -path '*/target/dependency-check/*' -exec cp -r {{}} {reports_dir} \\;")

    if Path("target/dependency-check").exists():
        run_cmd(f"cp -r target/dependency-check/* {reports_dir}/")

    # Step 7: Commit & push changes
    run_cmd("git add .")
    run_cmd('git commit -m "Agent 1: Vulnerability Assessment Report"', check=False)
    run_cmd(f"git push origin {branch_name}")

    # Step 8: Create Pull Request (Agent 3)
    print("=== Creating Pull Request ===")

    pr_title = f"Security OSS Vulnerability Discovery [{base_branch}]"
    pr_body = f"""
### Automated Dependency Report

This Pull Request was generated automatically following a push to **{base_branch}**.

**Details:**
- **Origin Branch:** {base_branch}
- **Feature Branch:** {branch_name}
- **Status:** Agent 1 has successfully generated a vulnerability report.

*Please review the 'reports/owasp' directory in this branch for full findings.*
"""

    run_cmd(
        f'gh pr create '
        f'--base {base_branch} '
        f'--head {branch_name} '
        f'--title "{pr_title}" '
        f'--body "{pr_body}"'
    )

    print("=== OSS Upgrade Agent Completed ===")


if __name__ == "__main__":
    main()