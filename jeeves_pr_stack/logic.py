import json
import sys
from dataclasses import dataclass

import sh

from jeeves_pr_stack.models import Commit, PullRequest


@dataclass
class JeevesPullRequestStack:
    """Jeeves PR Stack application."""

    gh: sh.Command
    git: sh.Command

    def list_commits(self) -> list[Commit]:
        """List commits for current PR."""
        raw_commits = json.loads(self.gh.pr.view(json='commits'))['commits']

        return [
            Commit(
                oid=raw_commit['oid'],
                title=raw_commit['messageHeadline'],
            )
            for raw_commit in raw_commits
        ]

    def split(
        self,
        pull_request_to_split: PullRequest,
        splitting_commit: Commit,
        new_pr_branch_name: str,
    ):
        """Split a pull request into two smaller ones."""
        self.git.checkout(splitting_commit.oid)

        self.git.switch('-c', new_pr_branch_name)
        self.gh.pr.create(
            '--fill',
            base=pull_request_to_split.base_branch,
            assignee='@me',
            _in=sys.stdin,
            _out=sys.stdout,
        )

        self.gh.pr.edit(pull_request_to_split.number, base=new_pr_branch_name)
