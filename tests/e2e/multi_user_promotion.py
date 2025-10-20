"""Manual E2E scenario for promotion batch validation.

Steps:
1. Seed three personal knowledge entries for distinct users in the same team using the MCP server.
2. Run `services/mcp-server/scripts/promote.py TEAM_ID --dry-run` and verify summary shows candidates.
3. Run without `--dry-run`, confirm new team knowledge nodes exist and PromotionAudit entries created.
4. Execute `/api/knowledge/search` for another team member and assert promoted knowledge is discoverable.

This placeholder file exists to ensure automated tooling recognises the E2E scenario path.
"""

SCENARIO_DESCRIPTION = "US3 promotion batch validation scenario"
