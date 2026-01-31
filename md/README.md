# Tasks

Use this folder as the single source of truth for implementation tasks.

------------------------------------------------------------------------

## Project Context

Agents must operate with a **product-oriented mindset**:

-   Always prioritize real functionality over theoretical design.
-   Optimize for production readiness.
-   Prefer simple, testable implementations.
-   Avoid overengineering.

The agent is responsible for continuously improving the system through
execution, testing, and analysis.

------------------------------------------------------------------------

## Owner Requirements

-   The app must allow anyone to create an account and track their own
    progression.
-   Provide a test account for owner review when requested.

------------------------------------------------------------------------

## Files

-   `backlog.md` --- prioritized task list\
-   `active.md` --- tasks currently in progress\
-   `done.md` --- completed tasks (short notes)

------------------------------------------------------------------------

## Workflow

------------------------------------------------------------------------

### 0) Operational Awareness (MANDATORY)

Before picking or executing tasks, the agent must:

1.  Review the current state of the repository.
2.  Understand existing architecture.
3.  Identify broken flows, missing logic, or technical risks.
4.  Favor changes that improve **stability, clarity, and production
    readiness**.

The agent must think like a **senior engineer owning the product**.

------------------------------------------------------------------------

### 1) Task Creation

When adding tasks to `backlog.md`:

Each task MUST:

-   Improve the product
-   Strengthen the core user flow
-   Reduce technical risk
-   Move the system toward production readiness

Good task categories:

-   Missing core features\
-   Logic flaws\
-   Security gaps\
-   Performance risks\
-   Observability improvements\
-   UX blockers\
-   Infrastructure readiness

Avoid:

-   Cosmetic refactors without value\
-   Premature abstractions\
-   Experimental rewrites

------------------------------------------------------------------------

### 2) Autonomous Execution Loop

The agent must operate continuously:

1)  Pick the highest-value task from `backlog.md` → move to `active.md`\
2)  Implement the task\
3)  Test the behavior\
4)  Check logs for errors\
5)  Fix any discovered issues immediately\
6)  Repeat until the system is stable

When finished → move task to `done.md` with completion date.

No waiting. No permission required.

------------------------------------------------------------------------

### 3) Mandatory Validation After EVERY Task

The agent MUST:

#### ✅ Run Tests

-   Unit tests (if present)
-   Integration paths
-   API flows
-   Critical user journeys

#### ✅ Inspect Logs

Look for:

-   Exceptions\
-   Silent failures\
-   Retry storms\
-   DB errors\
-   Auth issues

If errors exist → **fix before continuing.**

------------------------------------------------------------------------

#### ✅ Cleanup Scan

Remove:

-   unused code\
-   dead configs\
-   duplicate logic\
-   unnecessary abstractions

Enforce:

-   KISS\
-   DRY\
-   SOLID

------------------------------------------------------------------------

#### ✅ Rebuild System

Always rebuild after changes:

-   frontend build\
-   backend restart\
-   Docker compose\
-   migrations

Every change must run on compiled assets --- never assume correctness.

------------------------------------------------------------------------

### 4) Continuous Improvement Loop (CRITICAL)

Before starting the next task, the agent MUST:

1.  Review the application holistically.
2.  Analyze system logic.
3.  Detect weaknesses such as:

-   fragile architecture\
-   poor UX\
-   missing flows\
-   scaling risks\
-   security concerns

Then:

✅ Propose improvements\
✅ Add them to `backlog.md`\
✅ Continue execution

The agent is expected to behave like a **self-directing product
engineer**.

------------------------------------------------------------------------

### 5) Backlog Empty Rule (VERY IMPORTANT)

If `backlog.md` becomes empty:

The agent MUST immediately perform a **full product analysis**:

-   User journey
-   Core mechanics
-   Failure scenarios
-   Abuse vectors
-   Production risks
-   Operational visibility

Then:

1.  Generate a new backlog.
2.  Prioritize by impact.
3.  Resume execution loop.

The system must **never stall**.

------------------------------------------------------------------------

## Absolute Rule

> **Read backlog → execute → test → check logs → fix → analyze →
> generate improvements → repeat.**

No idle state is allowed.
