# Canonical harness reports for the admin API and community docs.
#
# Keep:
#   phase5_eval_summary.json      — GET /api/admin/eval-summary skills + adversarial
#   token_budget_report.{json,md} — progressive vs monolithic token comparison
#   regression_eval_report.{json,md}
#   adversarial_routing_report.md — EDD before/after centerpiece
#   edd_multistep_refactor_notes.md
#   full_eval_report.md
#
# Do not commit ephemeral CLI dumps (*.txt). They are gitignored; regenerate
# reports with the harness scripts under backend/harness/.
