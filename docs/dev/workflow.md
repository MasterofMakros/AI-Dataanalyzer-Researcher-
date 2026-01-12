# Project Workflow

## Guiding Principles
1. **Git is the Audit Trail**: Every file operation is logged and committable
2. **Copy First, Delete Never**: Source (D:) stays intact until F: is verified
3. **AI Context is Mandatory**: Every new folder gets a `_context.md`
4. **Hash Before Move**: SHA256 verification prevents silent corruption

## Task Workflow (File System Operations)

### Standard Operation Flow
1. **Document Intent**: Update `plan.md` with the planned operation
2. **Mark In Progress**: Change task from `[ ]` to `[~]`
3. **Execute with Logging**: Run PowerShell script that logs to manifest
4. **Verify Integrity**: Compare hashes, check file counts
5. **Git Commit**: Commit manifest changes with descriptive message
6. **Mark Complete**: Update task to `[x]` with commit SHA

### Rollback Procedure
1. **Identify Bad Commit**: `git log` in `F:\.migration_manifest`
2. **Revert Manifest**: `git revert <commit>`
3. **Execute Undo Script**: Read reverted manifest, delete bad files
4. **Restore from D:**: Re-copy affected files from source

## Quality Gates (Before Marking Complete)
- [ ] Hash verification passed (source == destination)
- [ ] File count matches expected
- [ ] `_context.md` present in new folders
- [ ] No orphaned files in `_Inbox`
- [ ] Git commit created with proper message

## Commit Message Format
```
<type>(<scope>): <description>

Types: migrate, structure, fix, docs, cleanup
Scope: pool-name or global
```

### Examples
```bash
git commit -m "migrate(mediathek): Copy Video folder with verification"
git commit -m "structure(inbox): Add Telegram subfolder"
git commit -m "fix(manifest): Correct hash mismatch in batch 5"
```

## Emergency Procedures

### Corrupted File Detected
1. Check `errors.log` in manifest repo
2. Locate source file on D:
3. Verify source integrity with hash
4. Re-copy single file to F:
5. Update manifest

### Disk Full
1. Stop all copy operations
2. Identify largest folders
3. Prioritize critical data pools (09, 10)
4. Move non-essential to external backup
