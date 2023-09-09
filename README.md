# `jeeves-pr-stack`

`jeeves-pr-stack` is a plugin for [jeeves](https://jeeves.sh) that helps manage stacks of GitHub pull requests. It aims to simplify the code review process by organizing pull requests that depend on each other.

## Installation

```shell
poetry add --group dev jeeves-pr-stack
```

## Motivation

While pull requests are a powerful tool for code review, they tend to become larger and larger, and thus more difficult for the reviewer to tackle.

One possible way to resolve that is to split implementation of a feature into two or more pull requests. For instance,

* PR `#42` **Backend for the Super Feature** directed from `super-feature-backend` branch to `main` branch,
* and PR `#43` **Frontend for the Super Feature** directed from `super-feature-frontend` branch to `super-feature-backend` branch.

The PRs are written in such a way that the first of them can be independently merged to `main` and deployed without breaking the system. This makes the process of code review faster and easier, and allows to deploy more often.

Let's call such structures **PR Stacks**.

### Caveats

Managing PR Stacks manually can be tedious; for instance, every time when changing `#42` you need to rebase `#43`. It becomes particularly annoying when the length of the stack is more than 2.

`jeeves-pr-stack` comes to the rescue.

## Commands

### `j stack`

View the current PR Stack.

### `j stack push`

* Create a new PR in current branch if none exists, or use the one that is there,
* And set the base branch of this PR to point to another open PR in the repository, stacking one PR on top of another.

### `j stack pop`

* Fetch the bottom-most PR of current stack,
* Merge it into the repository main branch,
* Redirect the follow-up PR to point to the main branch so as to make it mergeable,
* And delete the branch of the PR that was merged.
