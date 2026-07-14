"""Demo-only code executor for bundled skill scripts.

UnsafeLocalCodeExecutor runs Python in a local subprocess with no sandbox.
This project uses it only for trusted, author-written dummy scripts under
skills/*/scripts/. Never enable this for untrusted or production workloads.
"""

from google.adk.code_executors.unsafe_local_code_executor import (
    UnsafeLocalCodeExecutor,
)

demo_code_executor = UnsafeLocalCodeExecutor()