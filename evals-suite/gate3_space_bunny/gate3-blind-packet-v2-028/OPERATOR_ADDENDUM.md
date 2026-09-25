# Operator correction received after packet dispatch

The operator reports that the CP4 prompt was accidentally submitted twice: the first run was interrupted, and the prompt was then submitted again. This may explain the residual `__pycache__/query.cpython-314.pyc` in the observed workspace. The screenshot and workspace snapshot do not independently establish when or by which run the cache file was created.

The active tab was new relative to the CP1–CP3 conversation, but the second CP4 invocation may have had visible context or workspace changes from the interrupted first invocation. The available evidence does not establish whether the first invocation changed code. Record this as a limited protocol deviation rather than claiming a pristine one-shot CP4 takeover.

The original submitted snapshot, its tree hash, and all bridge results remain unchanged. Assess functional acceptance from the trusted checks. Treat the cache as an observed artifact, while separating its presence from attribution of fault to the candidate. This addendum is a post-dispatch correction, not part of the original sealed submission.
