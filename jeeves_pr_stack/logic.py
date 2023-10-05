import json
import sys
from dataclasses import dataclass
from functools import cached_property
from typing import Iterable

import sh

from jeeves_pr_stack import github
from jeeves_pr_stack.errors import MergeConflicts
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

    @cached_property
    def starting_branch(self):
        """Branch in which the app was started."""
        return self.git.branch('--show-current').strip()

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

    def rebase(self) -> Iterable[PullRequest]:
        """Rebase all PRs in current stack."""
        stack = github.retrieve_stack(self.starting_branch)

        for pr in stack:
            yield pr

            self.git.switch(pr.branch)
            self.git.pull()

            try:
                self.git.pull.origin(pr.base_branch, '--rebase')
            except sh.ErrorReturnCode as err:
                standard_output = err.stdout.decode()

                if 'Merge conflict in' in standard_output:
                    raise MergeConflicts()

                raise

            self.git.push('--force')

        self.git.switch(self.starting_branch)
