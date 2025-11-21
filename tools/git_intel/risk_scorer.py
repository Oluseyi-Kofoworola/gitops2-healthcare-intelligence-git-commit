import subprocess
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import List


CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "git-forensics-config.yaml"


@dataclass
class Commit:
    sha: str
    message: str
    files: List[str]


class RiskScorer:
    def __init__(self, config_path: Path = CONFIG_PATH):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

    def get_recent_commits(self, max_count: int = 50) -> List[Commit]:
        cmd = [
            "git",
            "log",
            f"--max-count={max_count}",
            "--pretty=format:%H%x1f%s",
            "--name-only",
        ]
        raw = subprocess.check_output(cmd, text=True)
        lines = raw.splitlines()

        commits: List[Commit] = []
        current: Commit | None = None

        for line in lines:
            if not line:
                continue
            if "\x1f" in line:
                # New commit header
                if current:
                    commits.append(current)
                sha, msg = line.split("\x1f", 1)
                current = Commit(sha=sha, message=msg.strip(), files=[])
            else:
                if current:
                    current.files.append(line.strip())

        if current:
            commits.append(current)
        return commits

    def score_commit(self, commit: Commit) -> float:
        score = 0.0

        # Semantic weight based on type
        semantic_weights = self.config.get("semantic_weights", {})
        ctype = self._extract_type(commit.message)
        score += semantic_weights.get(ctype, 0.1) * 0.5

        # Critical path impact
        critical_paths = self.config.get("critical_paths", {})
        critical_score = 0.0
        for path, meta in critical_paths.items():
            for f in commit.files:
                if f.startswith(path):
                    critical_score = max(
                        critical_score, meta.get("business_criticality", 0.0)
                    )
        score += critical_score * 0.5

        return min(score, 1.0)

    @staticmethod
    def _extract_type(message: str) -> str:
        # naive parse of conventional commit type
        if ":" not in message:
            return "other"
        head = message.split(":", 1)[0]
        if "(" in head:
            return head.split("(", 1)[0]
        return head


def main() -> None:
    scorer = RiskScorer()
    commits = scorer.get_recent_commits(max_count=50)

    if not commits:
        print("No commits found. Initialize a git repo and create some commits.")
        return

    print("Analyzing last 50 commits...\n")

    for c in commits:
        score = scorer.score_commit(c)
        if score >= 0.7:
            label = "HIGH"
        elif score >= 0.4:
            label = "MEDIUM"
        else:
            label = "LOW"
        print(f"[{label}] {score:.2f}  {c.message} ({c.sha[:8]})")


if __name__ == "__main__":
    main()
