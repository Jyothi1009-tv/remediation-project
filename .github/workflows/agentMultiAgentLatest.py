import os
import subprocess
import sys
from pathlib import Path
import json
import shutil
import google.generativeai as genai

# -----------------------------
# COMMON UTILITIES
# -----------------------------
def run_cmd(cmd, check=True):
    print(f"\n>>> {cmd}")
    result = subprocess.run(cmd, shell=True, text=True)
    if check and result.returncode != 0:
        print(f"FAILED: {cmd}")
        sys.exit(result.returncode)
    return result


def get_env(var):
    value = os.environ.get(var)
    if not value:
        print(f"Missing required env variable: {var}")
        sys.exit(1)
    return value


# -----------------------------
# GEMINI SETUP
# -----------------------------
def init_gemini():
    api_key = get_env("GEMINI_API_KEY")
    genai.configure(api_key=api_key)

    return genai.GenerativeModel(
        model_name="gemini-2.5-flash"
    )


# -----------------------------
# AGENT 1: DISCOVERY
# -----------------------------
class Agent1Discovery:
    def run(self):
        print("\n=== Agent 1: Discovery ===")

        base_branch = get_env("GITHUB_REF_NAME")

        commit_id = subprocess.check_output(
            "git rev-parse --short HEAD", shell=True
        ).decode().strip()

        branch_name = f"feature/{base_branch}-{commit_id}"

        run_cmd('git config --global user.email "agent@automation.com"')
        run_cmd('git config --global user.name "OSS agent"')

        run_cmd(f"git checkout -b {branch_name}")
        run_cmd("mvn clean install")
        run_cmd("mvn verify org.owasp:dependency-check-maven:check")

        # ✅ Collect reports properly
        reports_dir = Path("reports/owasp")
        reports_dir.mkdir(parents=True, exist_ok=True)

        print("\nCollecting OWASP reports from all modules...")

        for dep_dir in Path(".").rglob("target/dependency-check"):
            module_name = dep_dir.parent.parent.name
            dest = reports_dir / module_name

            print(f"Copying {dep_dir} -> {dest}")
            shutil.copytree(dep_dir, dest, dirs_exist_ok=True)

        print("✅ Reports collected from all modules")

        return branch_name, base_branch


# -----------------------------
# AGENT 2: ANALYSIS (GEMINI)
# -----------------------------
class Agent2Analysis:
    def __init__(self):
        self.model = init_gemini()

    def load_report(self):
        folder = Path("reports/owasp")

        # ✅ search recursively
        json_files = list(folder.rglob("*.json"))

        if not json_files:
            print("No JSON report found, analysis skipped")
            return None

        print(f"Using report: {json_files[0]}")

        with open(json_files[0]) as f:
            return json.load(f)

    def summarize_with_gemini(self, report):
        print("\n=== Agent 2: Gemini Analysis ===")

        prompt = f"""
Analyze this OWASP Dependency Check report and provide:

1. Critical vulnerabilities summary
2. High-risk dependencies
3. Suggested upgrades/fixes
4. Overall risk score (Low/Medium/High)

REPORT:
{json.dumps(report)[:15000]}
"""

        response = self.model.generate_content(prompt)
        return response.text

    def run(self):
        report = self.load_report()
        if not report:
            return "No vulnerabilities found or report missing."

        summary = self.summarize_with_gemini(report)

        Path("reports").mkdir(exist_ok=True)

        with open("reports/analysis_summary.md", "w") as f:
            f.write(summary)

        return summary


# -----------------------------
# AGENT 3: PR CREATION
# -----------------------------
class Agent3PR:
    def run(self, base_branch, branch_name, analysis_summary):
        print("\n=== Agent 3: PR Creation ===")

        run_cmd("git add .")
        run_cmd(
            'git commit -m "Agent: Vulnerability Report + Analysis"',
            check=False,
        )
        run_cmd(f"git push origin {branch_name}")

        pr_title = f"Security OSS Analysis [{base_branch}]"

        pr_body = f"""
## 🔐 Automated OSS Vulnerability Report

### Branch Info
- Base: {base_branch}
- Feature: {branch_name}

---

### 🤖 AI Analysis (Gemini)

{analysis_summary[:5000]}

---

### 📂 Reports
- OWASP Reports: `reports/owasp/`
- AI Summary: `reports/analysis_summary.md`
"""

        run_cmd(
            f'gh pr create '
            f'--base {base_branch} '
            f'--head {branch_name} '
            f'--title "{pr_title}" '
            f'--body "{pr_body}"'
        )


# -----------------------------
# MAIN
# -----------------------------
def main():
    print("=== Multi-Agent OSS Security System ===")

    agent1 = Agent1Discovery()
    branch_name, base_branch = agent1.run()

    agent2 = Agent2Analysis()
    summary = agent2.run()

    agent3 = Agent3PR()
    agent3.run(base_branch, branch_name, summary)

    print("\n=== COMPLETE ===")


if __name__ == "__main__":
    main()