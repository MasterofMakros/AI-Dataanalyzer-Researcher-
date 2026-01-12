## FEATURE:
[A clear, concrete description of the feature or change. What does it do? What are the constraints?]
- e.g. "Implement a robust API endpoint for uploading files that handles duplicates."
- **Non-Goals:** What are we NOT doing?

## EXAMPLES:
[List specific files in `examples/` or existing code that demonstrate the pattern to use.]
- `examples/cli_pattern.ps1`: Use this for argument parsing.
- `docker/conductor-api/api_service.py`: Use this for FastAPI structure.

## DOCUMENTATION:
[Links or instructions on where to find necessary context.]
- `docs/agent/reference/services.md`: For port mappings.
- `docs/architecture.md`: For data flow.

## OTHER CONSIDERATIONS:
- **Platform:** Windows Host + Docker Desktop.
- **Performance:** Handle large files (>1GB).
- **Security:** No hardcoded secrets.
- **Validation:** Must pass `scripts/validate.ps1`.
