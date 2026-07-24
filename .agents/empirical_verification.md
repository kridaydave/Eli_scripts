# Autonomous Technical Skepticism & Empirical Verification

1. **Verify Before Concluding**: Never declare a root cause, trend, or bug fix based on early or partial data (e.g., single pass@1 success or unverified loss drop). Frame initial observations strictly as hypotheses.
2. **Isolate Variables Autonomously**: Actively propose and execute minimal, isolated diagnostic tests (standalone scripts, full-dataset greps, exact prompt inspects) to prove or disprove hypotheses without requiring user prompting.
3. **No Speculative Citations**: Only cite line numbers, file contents, or parameters that have been directly inspected via tools in the current trajectory.
4. **Distinguish Capability vs. Format**: When evaluating ML model outputs or system failures, explicitly separate capability gaps from formatting/parser mismatches.
