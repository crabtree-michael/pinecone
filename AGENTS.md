# llm Directory

The `llm` directory contains context for developing the proposed system. Users will modify the `llm` to describe to

There are two types of files:

1. `*.llm.md` which provides a description of project objectives, architecture, and decisions.

2. `*.llm.yaml` provides specific implementation details for files.

When these files reference one another only lo

**Do not modify any file in the llm directory**, however you may

# Workflow

Your workflow is as follows:

1. Create a safe git sandbox environment. This primarily means insuring you are working on a `llm` prefixed branch. If you are not on one you can create one. For branches use the naming format: `llm-{model}-{timestamp}`,

2. Read git diff of `llm` directory to determine a plan. If it is a small change, you can go straight to step 3. Otherwise, verify the plan and implementation details with user. If part of the proposed details are unclear in the git diff, ask follow up questions. Based on follow up questions you can propose changes to the `.llm` files, but do not modify the files.

3. Implement the proposed changes. Your implementation should be as strict to the implementation details as possible. The following should be prioritized in the implementation:

- Correctness
- Modularity

4. Commit the proposed changes to git.


# Commands

1. `continue`: User wants the llm to continue current execution. If no next steps in plan, the workflow should be restarted.

