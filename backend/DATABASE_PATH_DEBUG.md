# Parts Database Path Issue

## Problem

The parts database files exist locally at `backend/app/data/parts/` but Railway can't find them at `/app/app/data/parts`.

## Why This Happens

Railway's deployment structure:

- Railway copies `backend/` contents to `/app`
- So `backend/app/data/parts/` → `/app/app/data/parts/`
- But the path resolution might not be finding it

## Possible Causes

1. **Files not deployed** - Check if `app/data/parts/*.json` files are gitignored
2. **Path resolution timing** - Path might be checked before files are available
3. **Railway structure differs** - Railway might structure files differently

## Current Fix

Enhanced path resolution to:

- Check if directory exists AND has JSON files
- Try multiple Railway-specific paths
- Log all attempted paths for debugging
- Continue running even if not found (non-critical)

## How to Verify Files Are Deployed

After deploy, check Railway logs for:

```
Found parts database at: /app/app/data/parts (11 files)
```

If you see "Parts database path not found", the files aren't being deployed.

## Solution: Ensure Files Are Committed

Make sure `app/data/parts/*.json` files are:

1. ✅ Committed to git
2. ✅ Not in `.gitignore`
3. ✅ Pushed to the repo Railway is deploying from

## Non-Critical

The app will run without the database - it just won't have parts data. The database warning is non-critical.
