# Agent instructions for The Big Short

## Before changing anything

0. Never create or change README.md without my explicit consent. Keep README drafts in chat. Your writing is AI-Slop.
1. Inspect the repository tree, Git status, current code, tests, and relevant project documents. Preserve unrelated work.
2. State the task's input, expected output, acceptance check, and smallest affected layer. Surface missing metadata or scientific assumptions before using them.
3. Reuse existing validation, preprocessing, analysis, and export functions. Search before adding a new abstraction.
4. For a multi-step change, write a brief plan with a check after each step. Keep issues and pull requests focused; aim for a reviewable diff, usually under 500 changed lines. Split by behavior, not arbitrary line count.

## Code comments

- Never use inline comments. Use a standalone scope comment in the form `#-----Scope of the function being defined----` where a comment is needed.
- Do not comment every function. In notebooks, reserve comments for the most important functions.

## Assignment requirements

- Follow PLAN.md, using the existing FastAPI, LiteLLM, Gemini, and single HTML starter. No new frameworks or dependencies.
- Remember conversations within sessions and keep separate sessions isolated.
- Provide at least three well-described tools, including external data access and one original tool per team member. This solo project has four tools, including liquidity_check and call_my_bluff as original candidates; class-wide uniqueness requires comparison with other submissions.
- Describe tool names and arguments clearly. Return actionable errors to the model.
- Preserve the /chat response fields: response, session_id, and tool_calls, with name, args, and result for every call. Show calls in the UI.
- Give the agent a distinct frontend and three sample grader queries in the README draft.
- Simulate only. Never place trades. Report partial fills and excluded fees. Market-implied odds are not certain probabilities.
- Review finished code with the moyu skill and remove unnecessary complexity within the requested scope.

## Writing preferences

- Avoid long dashes in documents, Markdown, and output text unless necessary.
- When drafting with the Gmail connector, use only 'best, Luca' as the signature.
