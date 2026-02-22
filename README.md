# MedLog One-Click (Obsidian Plugin)

MedLog One-Click is a production-ready Obsidian community plugin for one-click daily medication and vitals logging with TSV export.

## Features

- **MedLog: Log AM meds**: one click logs all meds with `"AM"` schedule.
- **MedLog: Log PM meds**: one click logs all meds with `"PM"` schedule.
- **MedLog: Log PRN med…**: opens modal with PRN-only presets.
- Optional **one-click PRN commands**: `MedLog: PRN — <label>` for each PRN med.
- **MedLog: Log vitals…**: prompts for HR/BP/notes and appends to vitals table.
- **MedLog: Export TSV**: exports `exports/meds.tsv` and `exports/vitals.tsv`.

## Date/Time Format

- Daily filename format default: `DD-MM-YYYY` (e.g. `22-02-2026.md`).
- Table row timestamp format: `DD-MM-YYYY HH:mm` (e.g. `22-02-2026 07:35`).
- Uses Obsidian `moment` with local time.

## Expected Daily Note Structure

Medication table:

```md
| ts | med | dose | unit | hr | bp_sys | bp_dia | notes |
|---|---|---:|---|---:|---:|---:|---|
<!-- MED_LOG -->
```

Vitals table:

```md
| ts | hr | bp_sys | bp_dia | notes |
|---|---:|---:|---:|---|
<!-- VITALS_LOG -->
```

If markers are missing in an existing daily note, the plugin appends missing table header + marker and continues.

## Default Settings

- `dailyFolder`: `Medical Daily`
- `dailyFilenameFormat`: `DD-MM-YYYY`
- `dailyTemplatePath`: `Templates/Medical Daily Note.md`
- `medMarker`: `<!-- MED_LOG -->`
- `vitalsMarker`: `<!-- VITALS_LOG -->`
- `enableOneClickPrnCommands`: `true`
- `exportsFolder`: `exports`
- `includeSourceFileInExport`: `true`
- `meds`: default preset list included (placeholders only; no medical advice).

## Install (Manual Dev)

1. Clone this repo.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Build:
   ```bash
   npm run build
   ```
4. Copy `main.js`, `manifest.json`, `styles.css` into your vault’s plugin directory:
   `.obsidian/plugins/medlog-oneclick/`
5. Enable **MedLog One-Click** in Obsidian Community Plugins.

## Commands

- `MedLog: Log AM meds`
- `MedLog: Log PM meds`
- `MedLog: Log PRN med…`
- `MedLog: Log vitals…`
- `MedLog: Export TSV`
- Optional generated commands: `MedLog: PRN — <label>`

## Export Details

On export:
- Scans markdown files under `dailyFolder`.
- Parses medication rows (`8` columns) and vitals rows (`5` columns) from marker sections.
- Writes:
  - `exports/meds.tsv`
  - `exports/vitals.tsv`
- Headers include `source_file` when enabled.
- Tabs/newlines are sanitized to spaces.

## Release Workflow

GitHub Actions workflow in `.github/workflows/release.yml` runs on tag `v*`:
- `npm ci`
- `node scripts/sync-version.mjs`
- validates `manifest.json` version matches tag (without `v`)
- `npm run build`
- `node scripts/zip.mjs`
- creates GitHub Release and uploads:
  - `main.js`
  - `manifest.json`
  - `styles.css`
  - `medlog-oneclick.zip`

## Acceptance Test Checklist

1. With no existing daily note, run **MedLog: Log AM meds**:
   - today’s file is created from template if present, fallback if missing;
   - AM rows append under `<!-- MED_LOG -->`.
2. Run **MedLog: Log vitals…**:
   - appends one vitals row under `<!-- VITALS_LOG -->`.
3. Remove marker(s) in an existing note and run commands:
   - plugin appends missing marker + table header and logs rows without crash.
4. Paste invalid meds JSON in settings:
   - Notice shows validation error;
   - existing settings remain intact.
5. Run **MedLog: Export TSV**:
   - creates `exports/meds.tsv` and `exports/vitals.tsv` with correct headers/rows.

## License

MIT
