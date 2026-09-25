# Fresh-session evidence, scope-limited

The operator supplied a UI screenshot before reporting the CP4 result. Its original bytes are preserved outside this blind packet with SHA-256 `49ebcba95739db2acf45cbf3cae612747c8ecfe0bcadb23e6487c87c5ada071c`.

The screenshot shows two separate application tabs, with the active tab containing the CP4 takeover prompt. No CP1–CP3 chat messages are visible in that active tab. The operator states that this was a newly opened session and that prior chat history was not carried over. The unredacted image is excluded here because it displays the agent/model UI and would compromise blind review.

This supports a limited finding of **separate visible conversation history**. It does not prove that the backend supplied no hidden system prompt, generic workflow instructions, memory, or other context; no cryptographic session transcript or wire-level context receipt was collected. Reading the existing repository files is allowed by the CP4 task and is not a violation of the fresh-chat condition.
