# SE Execution Scope

Read when invoking an SE skill directly or composing it in another workflow.
A skill has the same responsibility and subagent policy in both cases. Caller
identity does not enable, disable, or transfer that skill's delegation behavior.
Explicit user constraints and available capabilities still govern execution.

| Skill | Delegation policy |
| --- | --- |
| Implement, Adversarial Review, Review PR, Grilling Session, Learn, Idea | Perform their work in the executing session/task; create no tasks or subagents. |
| Spec | Own its planner and optional helpers under its planner contract. |
| Study | Own its controller and optional helpers under its surface and worker contracts. |
| Deliver | Own isolated workers through PR publication and CI under its local worker contract; the current task owns orchestration. |
| Deliver Features | Own its coordinator, implementation lanes and reviewers under its delivery contract. |

An orchestrator may launch an agent and assign it a skill that creates no agents.
That agent executes the skill; the skill does not launch another layer or change
its own profile. For example, Delivery assigns Implement to a developer and
Adversarial Review to a different reviewer. Standalone Implement also ends at
its implementation handoff; it does not acquire an independent-review workflow.

Passing exact scope, target, evidence, and established action authority is
composition. Asking the callee to behave as another orchestrator, move its
responsibilities to the caller, or silently disable its helpers is not. A caller
owns sequencing its own gates and consuming the callee's result; it does not
reinterpret a provider review result as accepted code or local work as delivery.

Continue an existing planner/controller as the same invocation; do not rerun
its setup or create a second controller. Helpers may not recursively invoke an
orchestrating skill in violation of their assignment. If required orchestration
is unavailable or forbidden, use only the skill's documented fallback or return
the capability/authority conflict to its caller. Do not invent a different
standalone-versus-composed workflow to conceal it.
