# Agentic Engineering Framework

Operational controls for AI-assisted development. Two layers: **outer harness** (agent behavior) and **inner harness** (software correctness).

> `.agent/` is a project convention, not an industry standard. Adapt to your tools and workflow.

---

## 1. Repository Structure

```
.agent/
├── boot.md              # What agents read at startup
├── rules.md             # Agent behavior rules (outer harness)
├── quality.md           # Code quality standards (inner harness)
└── memory/
    ├── current-state.md # Project state
    ├── known-issues.md  # Unresolved problems
    └── decisions.md     # Architecture decisions
```

---

## 2. Agent Rules (Outer Harness)

**Before working:** Identify the active task, current branch, relevant files, and acceptance criteria. If anything is unclear, stop and ask.

**While working:**
- One task per session. Only modify task-relevant files.
- Don't invent requirements. Don't ignore failing tests. Don't delete tests to pass.
- If scope is unclear, stop and ask.

**Before finishing:** Report what you did, what changed, what passed, what failed, and what's risky.

---

## 3. Code Quality (Inner Harness)

Every production feature needs:
- Input/output validation
- Error handling with context-rich logging (no sensitive data)
- Tests for success, failure, and edge cases
- Timeout handling on external calls
- A known rollback path
- Observability for debugging

**A feature is done when it's implemented, tested, observable, and recoverable.**

---

## 4. Validation Gates

| Gate | When | Check |
|------|------|-------|
| **Scope** | Before coding | Task exists, criteria defined, branch matches task |
| **Code** | Before commit | No unrelated changes, no secrets, no dead code, no deleted tests |
| **Test** | Before commit | Unit tests pass, integration tests pass if affected, lint/build pass |
| **Review** | Before merge | Correctness, security, architecture consistency, regression risk |
| **Memory** | Before ending | Update `current-state.md`, `known-issues.md`, or `decisions.md` as needed |

---

## 5. Failure & Escalation

**When things break:** Report the exact failure, suspected cause, and recommended fix. Don't rewrite large modules for small bugs. Don't apply multiple speculative fixes at once. Fix one thing, validate, stop.

**Escalate when:** Architecture, data model, security boundaries, or public APIs would change. Requirements conflict. Test failures won't resolve. When in doubt, escalate — don't guess.

Escalation format: `Reason → Options → Recommendation → Risk → Files affected`

---

## 6. Enforcement

Don't rely solely on markdown files. Priority order:

1. **Automated checks** — pre-commit hooks, CI gates
2. **System prompt injection** — critical rules in the agent's prompt
3. **File-based instructions** — `.agent/` files
4. **Manual review** — human checklists

---

## 7. Rule Conflicts

When rules conflict, priority from highest to lowest:

1. **Security** — never commit secrets
2. **Safety** — never delete tests or hide failures
3. **Scope** — one task, relevant files only
4. **Process** — memory updates, handoff notes
5. **Style** — naming, formatting

Ambiguous requirements? Stop and escalate. Don't guess.

---

## 8. Memory Limitations

Agents may not read every file they're told to. Memory files are best-effort — useful for human continuity first, agent continuity second. Keep them short, structured, and front-load the critical information. Critical safety rules must also live in system prompts or CI, not only in files.

**Derive what you can from git.** Don't manually track branches, worktrees, or file changes — use `git branch`, `git worktree list`, `git diff`.

---

## 9. Worktrees (When You Need Parallel Work)

Use git worktrees to isolate parallel tasks. Each worktree gets one task, one branch, one agent writing at a time.

**Setup:**
```bash
git worktree add ../worktrees/TASK-014-reranking -b feature/TASK-014-reranking
cd ../worktrees/TASK-014-reranking
```

**Agent context:** Check `git branch --show-current` and optional `.worktree-context` file. If branch doesn't match the task, stop.

**Conflict prevention:** Rebase before merge. Minimize shared file changes. If two tasks can't be developed independently, they're one task.

**Cleanup:**
```bash
git worktree remove ../worktrees/TASK-014-reranking
```

---

## 10. Adoption

Start small, expand when useful:

1. **Start here:** Add agent rules file (`AGENTS.md` or `.agent/rules.md`). See if agents stay in scope.
2. **Add structure:** Task scripts, `.worktree-context`, branch-task validation.
3. **Add enforcement:** Pre-commit hooks, CI gates.
4. **Add quality standards:** Production feature checklist, test/observability expectations.
5. **Add domain rules:** RAG, multi-agent, or other domain-specific harnesses only when needed.
