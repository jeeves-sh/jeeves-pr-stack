import json
import os
import sys
from dataclasses import dataclass, field
from functools import cached_property
from typing import Iterable

import funcy
import sh

from jeeves_pr_stack import github
from jeeves_pr_stack.errors import MergeConflicts
from jeeves_pr_stack.models import Commit, PullRequest, RawPullRequest


@dataclass
class JeevesPullRequestStack:
    """Jeeves PR Stack application."""

    gh: sh.Command = field(
        default_factory=lambda: sh.gh.bake(
            _long_sep=None,
            _env={
                **os.environ,
                'NO_COLOR': '1',
            },
        ),
    )
    git: sh.Command = field(default_factory=lambda: sh.git)

    def list_pull_requests(
        self,
        author: str | None = None,
    ) -> list[PullRequest]:
        """
        Retrieve a list of all open PRs in the repo.

        Mark the one bound to current branch with `is_current` field.
        """
        fields = [
            'number',
            'baseRefName',
            'headRefName',
            'id',
            'isDraft',
            'mergeable',
            'title',
            'url',
            'reviewDecision',
            'reviewRequests',
            'statusCheckRollup',
        ]

        gh_pr_list = self.gh.pr.list.bake(json=','.join(fields))
        if author:
            gh_pr_list = gh_pr_list.bake(author=author)

        raw_pull_requests: list[RawPullRequest] = json.loads(
            gh_pr_list(),
        )

        return [
            PullRequest(
                is_current=(
                    raw_pull_request['headRefName'] == self.starting_branch
                ),
                number=raw_pull_request['number'],
                base_branch=raw_pull_request['baseRefName'],
                branch=raw_pull_request['headRefName'],
                title=raw_pull_request['title'],
                url=raw_pull_request['url'],
                is_draft=raw_pull_request['isDraft'],
                mergeable=raw_pull_request['mergeable'],
                review_decision=raw_pull_request['reviewDecision'],
                reviewers=funcy.pluck(
                    'login',
                    raw_pull_request['reviewRequests'],
                ),
                checks_status=github.construct_checks_status(raw_pull_request),
            )
            for raw_pull_request in raw_pull_requests
        ]

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
        stack = self.list_stack()

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

    def list_stack(self) -> list[PullRequest]:
        """
        List current stack.

        Order: from top branch to the main branch of the repository.
        """
        return github.construct_stack_for_branch(
            branch=self.starting_branch,
            pull_requests=self.list_pull_requests(),
        )
