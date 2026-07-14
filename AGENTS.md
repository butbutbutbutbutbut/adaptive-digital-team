# Agent Governance

- Maker and Checker responsibilities must remain separate.
- Self-acceptance is forbidden.
- Automatic merge is forbidden.
- Do not reset, force-push, or amend a submitted candidate.
- Do not commit secrets, private material, or unapproved binary assets.
- After the initial bootstrap commit, every change must use a separate branch and pull request.
- Rollback must use a new revert branch and a reviewed revert commit.
- Missing authority, state conflicts, or incomplete evidence must fail closed.
