Rangsit WaterWatch - automatic camera check every 5 minutes

INSTALL
1) Unzip this package.
2) Copy .github/workflows/water-check.yml into the website repository's .github/workflows/ folder.
3) Copy scripts/check_water.py into the website repository's scripts/ folder.
4) Ensure status.json is at the repository root (create an initial file if missing).
5) In GitHub repository Settings > Actions > General > Workflow permissions, select
   "Read and write permissions" so Actions can commit status.json.
6) Commit and push these files to main.
7) Open Actions > Rangsit WaterWatch Check > Run workflow to test immediately.

The workflow is scheduled every 5 minutes (GitHub scheduled workflows can be delayed).
It fetches the configured public camera snapshot, runs color-band analysis, and updates
status.json with level, fractions, check time and rolling 24-hour history.

IMPORTANT
- This requires the camera snapshot URL to be reachable from GitHub Actions runners.
- Your website index.html must fetch status.json from the repository/site root and parse
  these field names. The workflow does not modify index.html.
- Do not commit Telegram bot tokens or other secrets into the repository.
- A first reading is accepted immediately when no previous level exists; later changes
  require a second consecutive check, matching the C# source behavior.
