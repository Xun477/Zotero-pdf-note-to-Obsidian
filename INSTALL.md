# Installing Zotero pdf note to Obsidian (for an AI agent)

You are an AI agent and your user told you to install `Zotero pdf note to Obsidian`. This document
is the procedure. Follow it in order. Every step is safe to run again, and
every step names what to do when it fails. Commands are POSIX shell (macOS or
Linux). A Windows note follows each block that needs one.

The skill turns a Zotero paper PDF into a structured reading note and exports it
(Markdown + images) into an Obsidian paper vault. It depends on three external
services: **Zotero** (find the PDF), **MinerU** (extract text + figures), and
**Obsidian** (store the note). The whole install is six steps:

1. Find the skill directory for your harness.
2. Put the `Zotero pdf note to Obsidian` folder into it.
3. Install the Python dependencies.
4. Configure credentials (Zotero API key, MinerU token).
5. Configure the three filesystem paths.
6. Verify.

---

## Step 1: Find the skill directory for your harness

A skill is a folder your harness reads at startup. Each harness reads from a
fixed location:

| Harness | Skill directory (`TARGET`) |
| :-- | :-- |
| Claude Code | `~/.claude/skills/` |
| Codex | `~/.codex/skills/` |
| Pi, OpenCode | `~/.agents/skills/` |

Install into this global directory in the user's home, so the skill is available
in every project. Do not install into a project-local `.claude/skills` unless the
user explicitly asks to scope it to the current project.

Pick the row for the harness you are running in. If you cannot tell which harness
you are, decide by which config directory already exists:

```bash
ls -d ~/.claude ~/.codex ~/.agents 2>/dev/null
```

- `~/.claude` present -> use `~/.claude/skills/`
- `~/.codex` present -> use `~/.codex/skills/`
- `~/.agents` present -> use `~/.agents/skills/`

Create the directory so the rest of the steps have a target:

```bash
mkdir -p ~/.claude/skills   # replace with the TARGET for your harness
```

**If it fails:** a permission error means you are pointing at a directory you
cannot write. Confirm the path is under the user's home directory (`echo $HOME`),
not a system path.

> **Windows:** `~` is the user profile. The directories are
> `%USERPROFILE%\.claude\skills\`, `%USERPROFILE%\.codex\skills\`, and
> `%USERPROFILE%\.agents\skills\`. Create one with
> `mkdir "$env:USERPROFILE\.claude\skills"` in PowerShell.

---

## Step 2: Put the skill folder into the skill directory

The skill is the `Zotero pdf note to Obsidian` folder in this repository: a
`skill.md`, a `resources/` directory (`resources/template/` holds the note
templates, `resources/config/` holds the JSON config), and a `scripts/`
directory (the pipeline + export scripts). Copy the whole folder into `TARGET`.

### Path A: clone and copy (no extra tooling)

```bash
rm -rf /tmp/zpno-src
git clone --depth 1 https://github.com/luxiaxun70-creator/Zotero-pdf-note-to-Obsidian.git /tmp/zpno-src
mkdir -p ~/.claude/skills/"Zotero pdf note to Obsidian"   # replace with your TARGET
cp -R "/tmp/zpno-src/Zotero pdf note to Obsidian/." ~/.claude/skills/"Zotero pdf note to Obsidian"/
```

The copy overwrites any earlier install in place, so running it again just
refreshes the skill.

**If it fails:**
- `git: command not found` -> install git, or use Path B.
- Clone cannot reach GitHub -> check network access, then retry.
- After copying, confirm the skill and its scripts landed:
  ```bash
  ls ~/.claude/skills/"Zotero pdf note to Obsidian"/skill.md ~/.claude/skills/"Zotero pdf note to Obsidian"/scripts/pipeline_prep.py ~/.claude/skills/"Zotero pdf note to Obsidian"/resources
  ```
  If `skill.md` or `scripts/` is missing, the copy targeted the wrong path.
  Re-run the `cp` line and check `TARGET`.

### Path B: the skills CLI (third party)

`skills` is a third-party CLI for installing agent skills. It is not required.

```bash
npx -y skills add luxiaxun70-creator/Zotero-pdf-note-to-Obsidian
```

**If it fails** (the command is unavailable, or it does not place the folder under
your harness's skill directory): fall back to Path A, which needs only git.

> **Windows:** in PowerShell, replace the `cp -R` line with
> `Copy-Item -Recurse -Force "$env:TEMP\zpno-src\Zotero pdf note to Obsidian\*" "$env:USERPROFILE\.claude\skills\Zotero pdf note to Obsidian\"`
> and clone into `"$env:TEMP\zpno-src"`.

---

## Step 3: Install the Python dependencies

The scripts need Python 3.9+ and three packages. Check what is already present:

```bash
python3 --version
python3 -c "import httpx, PIL; print('ok')"
```

Then install what is missing (the skill itself never calls a network service
from your Python — MinerU does, via its own CLI, so `mineru-open-api` is also
needed):

```bash
pip install httpx Pillow mineru-open-api
```

**If it fails:** a `pip: command not found` means Python is not on PATH — install
Python 3.9+ from python.org, then retry. A permissions error means the user site
is not writable; prefer `pip install --user ...`.

> **Windows:** `python3` may be `python` on Windows. Run
> `python --version` and `python -m pip install httpx Pillow mineru-open-api`.

---

## Step 4: Configure credentials

Three credentials are required. The scripts read them from environment variables
(with a fallback file `~/.zotero_credentials`). Ask the user for each before
proceeding — the keys are secrets and never come from the repository.

### 4a. `ZOTERO_API_KEY` (required)

A Zotero Web API private key with **read** access. It is used to search the
library and locate the PDF attachment.

1. Open https://www.zotero.org/settings/keys
2. Click **Create New Private Key**.
3. Under "Personal Library", check **Allow notes access**. (Write access is
   optional — this skill only reads Zotero and writes the note to a local
   Obsidian vault, so it never needs the write permission. Grant read-only
   access for least privilege.)
4. Save and copy the 24-character key.

Set it:

```bash
export ZOTERO_API_KEY="your-24-char-key"
```

### 4b. `ZOTERO_USER_ID` (required — the default is the author's ID)

The numeric Zotero user ID appears at the top of the same keys page
("Your userID for use in API calls"). **You must set this — the script defaults
to the author's ID `21068406`, and using it would search the wrong library and
emit notes with the wrong `zotero` frontmatter link.**

```bash
export ZOTERO_USER_ID="your-numeric-user-id"
```

### 4c. `MINERU_TOKEN` (required)

A MinerU Open Platform API token, used for PDF text/figure extraction.

1. Register at https://mineru.net
2. Create an API token on the platform dashboard.
3. Set it:

```bash
export MINERU_TOKEN="your-mineru-token"
```

**Persisting credentials.** For a single session, `export` is enough. To make
them permanent:

- **macOS / Linux:** add the `export` lines to `~/.bashrc` / `~/.zshrc`, or write
  the fallback file the scripts also read:
  ```bash
  cat > ~/.zotero_credentials <<'EOF'
  ZOTERO_API_KEY=your-24-char-key
  ZOTERO_USER_ID=your-numeric-user-id
  EOF
  ```
- **Windows (PowerShell):** persist as user environment variables:
  ```powershell
  [System.Environment]::SetEnvironmentVariable('ZOTERO_API_KEY', 'your-24-char-key', 'User')
  [System.Environment]::SetEnvironmentVariable('ZOTERO_USER_ID', 'your-numeric-user-id', 'User')
  [System.Environment]::SetEnvironmentVariable('MINERU_TOKEN', 'your-mineru-token', 'User')
  ```
  New terminals inherit them. The Windows fallback also checks the registry
  (`HKCU\Environment`), and the file `%USERPROFILE%\.zotero_credentials`
  (format `API_KEY=...`).

---

## Step 5: Configure the three filesystem paths

The skill defaults to the author's local paths (`G:\硕士\...`). Every user must
point these at their own machine. Two ways to do it — **recommended: edit the
JSON config**, or **alternative: set environment variables** (which take
priority over the config file).

### 5a. Recommended: copy and edit the JSON config

Copy the shipped example into your local override (the local `config.json` is
git-ignored, so it will never be overwritten by an update):

```bash
cd "<TARGET>/Zotero pdf note to Obsidian"
cp resources/config/config.example.json resources/config/config.json
```

**Windows (PowerShell):**

```powershell
cd "$env:USERPROFILE\.claude\skills\Zotero pdf note to Obsidian"
Copy-Item resources\config\config.example.json resources\config\config.json
```

Then open `resources/config/config.json` and set the three paths (and optionally
`behavior`: `subdir`, `compress`, `model`, `timeout`). The scripts read it at
startup — no restart needed.

### 5b. Alternative: environment variables

Three environment variables override the config file (env > config.json >
built-in default). The scripts also accept equivalent CLI flags.

| Env var | What it is | CLI flag | Author default |
| :-- | :-- | :-- | :-- |
| `ZOTERO_STORAGE_DIR` | Where Zotero stores PDF attachments (`.../Zotero/storage`) | `--storage-dir` (pipeline_prep) | `G:\硕士\Zotero\storage` |
| `ZOTERO_NOTE_BASE_DIR` | Scratch dir for MinerU output + rewritten note | `--base-dir` (pipeline_prep) | `G:\硕士\ai\中转` |
| `OBSIDIAN_VAULT_DIR` | Obsidian vault root (note goes to `<vault>/文献/<paper>/`) | `--vault-dir` (export) | `G:\硕士\论文` |

How to find your values:

- **Zotero storage:** in Zotero open *Settings → Advanced → Files and Folders*,
  or check the Data Directory. The attachment folder is
  `<data-dir>/storage/`. Example: `/home/you/Zotero/storage` or
  `C:\Users\you\Zotero\storage`.
- **Obsidian vault:** wherever your vault folder is, e.g. `~/Documents/notes`.
  A `文献` subfolder is created under it automatically.

Set them (POSIX):

```bash
export ZOTERO_STORAGE_DIR="/home/you/Zotero/storage"
export ZOTERO_NOTE_BASE_DIR="/tmp/zotero-notes"
export OBSIDIAN_VAULT_DIR="/home/you/Documents/notes"
```

**Windows (PowerShell), permanent:**

```powershell
[System.Environment]::SetEnvironmentVariable('ZOTERO_STORAGE_DIR', 'C:\Users\you\Zotero\storage', 'User')
[System.Environment]::SetEnvironmentVariable('ZOTERO_NOTE_BASE_DIR', 'D:\zotero-notes', 'User')
[System.Environment]::SetEnvironmentVariable('OBSIDIAN_VAULT_DIR', 'D:\ObsidianVault', 'User')
```

---

## Step 6: Verify

Run the dependency check (from the installed skill folder):

```bash
bash -lc 'python3 -c "import httpx, PIL; print(\"deps ok\")"'
```

**Windows:**

```powershell
python -c "import httpx, PIL; print('deps ok')"
```

Then confirm the scripts parse their arguments (this proves the path env vars are
wired in — do **not** run a real extraction here, it calls the paid MinerU API):

```bash
python3 "<TARGET>/Zotero pdf note to Obsidian/scripts/pipeline_prep.py" --help
python3 "<TARGET>/Zotero pdf note to Obsidian/scripts/export_to_obsidian.py" --help
```

Both should print usage text. (Note: Python 3.8's argparse does **not** show
`(default: ...)` in `--help`, so confirm the config is wired by printing what
`load_config()` actually reads):

```bash
python3 -c "import sys; sys.path.insert(0, '<TARGET>/Zotero pdf note to Obsidian/scripts'); from load_creds import load_config; print(load_config())"
```

It should print a dict from `resources/config/`. To verify your override works,
edit `paths.base_dir` in your local `resources/config/config.json` (Step 5a)
and re-run the command — the printed `base_dir` should change to your value.
(Environment variables take priority at runtime, as documented in Step 5b.)

**If it fails:**
- `ModuleNotFoundError` -> the Python packages from Step 3 are missing.
- `ERROR: Cannot load ZOTERO_API_KEY` -> Step 4a was not done (or the fallback
  file is misnamed — the file must be `~/.zotero_credentials` with an
  `API_KEY=` line, not `ZOTERO_API_KEY=`).
- Permission errors on import -> the skill folder landed in a system path, not
  under the user's home (Step 1).

---

## Done

The skill is installed. From now on, the user just tells the agent the paper
title, for example:

> 整理这篇论文：*Advantages of measuring surface roughness with white light interferometry*

or in Claude Code:

```
/Zotero pdf note to Obsidian Advantages of measuring surface roughness with white light interferometry
```

The agent asks one question (paper type + whether to compress images), then runs
the pipeline automatically. See `README.md` for usage details, templates, and FAQ.

Common first-run problems, in brief:

- **MinerU times out / no .md produced** — the API can complete but the 120s
  client timeout fires first; check the output dir for a `.md` file and re-run.
- **Scanned PDF extracts garbage** — re-run with `--ocr`.
- **Wrong library searched** — `ZOTERO_USER_ID` is unset or still the author's
  default (Step 4b).
