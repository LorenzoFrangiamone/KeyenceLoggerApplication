# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Windows desktop Tkinter app ("Compare Export Agent" / `KCompareAgent`) for comparing two Keyence vision-inspection report folders and generating a Markdown changelog between them. It includes a local LLM (via `llama-cpp-python`) that proofreads/corrects the human-written changelog comment.

## Setup

```bash
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
pip install -r requirements.txt
```

Note: `requirements.txt` is UTF-16 encoded; tools that assume UTF-8 (e.g. `cat`/`grep`) will show it as garbled — read it with `iconv -f UTF-16 -t UTF-8` or PowerShell `Get-Content -Encoding Unicode` if inspecting it directly.

## Running

```bash
python Main.py
```

There is no test runner / CI configured. `tests/testAI.py` is a manual smoke-test script (not pytest) that exercises `AICorrection` directly — run it with `python tests/testAI.py`. It requires the GGUF model file to be present under `models/` (see below), so it will fail fast without it.

## Building the portable executable

`build_portable.bat` runs PyInstaller (using `KCompareAgent.spec`-equivalent flags: `--onedir --windowed --collect-all llama_cpp`) and then manually copies a model GGUF file into `dist/KCompareAgent/models/`. The model filename hardcoded in the batch script (`Qwen3-1.7B-Q4_K_M.gguf`) is currently stale relative to the model actually wired up in `src/AICorrector.py` (`qwen2.5-7b-instruct-q5_k_m-00001-of-00002.gguf`) — check `AICorrector.py`'s `MODEL_PATH` before relying on the batch script to copy the right file.

`build/` and `dist/` are gitignored output directories; `.gguf` model files are gitignored too (they're large binaries, must be obtained/placed manually under `models/`).

## Architecture

The app follows a strict front-end/back-end split, wired together only in `Main.py`. The UI itself is a `src/gui/` package (split out of a single 900-line `frontEnd.py` for maintainability — see breakdown below).

- **`src/backEnd.py`** — pure, UI-free logic. No Tkinter imports. Responsible for:
  - Locating and parsing report folder contents (`unit_*.csv`, `variable_*.csv`, `unit_*.txt`) via `load_report`.
  - Diffing two parsed reports: `compare_units`, `compare_variables`, `compare_unit_txt` (line-level diff of logic-block `.txt` files using `difflib.SequenceMatcher`).
  - Rendering diff results to Markdown (`render_units_changes`, `render_variables_changes`, `render_logic_changes`).
  - Top-level orchestration: `generate_changelog` (writes `ChangeLog_<A>_<B>.md` to disk) and `build_preview` (same rendering, returned as a string for in-app preview, no file write).
  - `validate_report_folder` checks a folder has the required `unit_*.csv` / `variable_*.csv` files before it's accepted in the UI.
  - `get_version` reads the application version out of a `variable_*.csv`'s `#Version`/`#Versione` row.
  - `append_change_record` appends a `[folder, version, comment]` row to a `Changes_*.csv` log (`;`-delimited), writing a header on first write and fixing a missing trailing newline before appending.

- **`src/gui/`** — the UI, split by responsibility:
  - **`app.py`** — `CompareApp(tk.Tk)`, the shell. Owns the two pages (`InputPage`, `PreviewPage`) and switches between them with `pack`/`pack_forget` (no multi-window flow). All business logic (`validate_fn`, `generate_fn`, `preview_fn`, `get_version`) is dependency-injected here from `Main.py` rather than imported directly inside the pages — keep that separation when extending the UI.
  - **`page_input.py`** — `InputPage`: pick Report A folder, Report B folder, output folder; live-validates via the injected `validate_fn` and enables "Next" only when both report folders pass validation. Calls `on_next(report_a, report_b, output_dir)` to hand control back to `app.py`.
  - **`page_preview.py`** — `PreviewPage`: calls the injected `preview_fn` to build a Markdown diff, renders it as HTML via `html_render.render_markdown` + `tkinterweb.HtmlFrame`, and hosts the "Comment" box, the `AIPanel`, "Generate Log" (`generate_fn`) and "Update Changes_*.csv" (`backEnd.append_change_record`).
  - **`ai_panel.py`** — `AIPanel`: the AI-assisted correction widget. Imports `AICorrection` directly from `src/AICorrector.py` (not injected, same as before). The correction call runs in a background `threading.Thread` and marshals results back to the UI via `self.after(...)`, since `llama-cpp-python` inference is slow and must not block the Tk mainloop.
  - **`html_render.py`** — single source of truth for Markdown→HTML rendering and the preview's CSS (previously duplicated near-identically in two places in `frontEnd.py`).
  - **`theme.py`** — shared colors/fonts constants.

- **`src/AICorrector.py`** — loads a local GGUF model via `llama_cpp.Llama` at import time (module-level singleton `llm`), using a system prompt from `src/promptCorrettore.txt`. `AICorrection(auto, human)` sends the auto-generated Markdown diff and the human comment as a single user message (`//AUTO\n...\n//HUMAN\n...`) and returns the model's `//Correzione:` / `//Suggerimento:` formatted reply (any `<think>...</think>` block is stripped). `MODEL_PATH` resolves relative to the executable directory when frozen (PyInstaller) vs. relative to the source tree otherwise — `Path(sys.executable).parent` vs `Path(__file__).resolve().parent.parent`. Because this module loads a multi-GB model at import time, anything importing `src/gui/ai_panel.py` (and transitively `src/gui/page_preview.py` / `src/gui/app.py`) pays that cost — keep that in mind if writing tests that only need `theme.py`, `html_render.py`, or `page_input.py`, which have no AI dependency and import cheaply.
  - `GPU_Nvidia = True` is a hardcoded flag inside `AICorrector.py` that selects GPU-offloaded (`n_gpu_layers=-1`, smaller `n_ctx`) vs. CPU-only (larger `n_ctx`) `Llama` init params — flip it manually if portability/GPU availability changes.

- **`docs/generateChangeLog.txt`** is the spec for the report folder format and changelog content/structure (file naming conventions, CSV column layouts for `unit_*.csv` and `variable_*.csv`, what ADDED+/REMOVED-/MODIFIED sections must contain). Treat it as the source of truth when changing diff/parsing logic in `backEnd.py`.
  - `docs/GenerateChangeLog.spec` references a `GenerateChangeLog.py` entry point that doesn't currently exist in the repo — it appears to be a leftover/older PyInstaller spec, not the one actually used (`KCompareAgent.spec` at the repo root targets `Main.py` and is the live one referenced by `build_portable.bat`).

## Domain notes (Keyence report folders)

A "report" is a folder named `report<id>` containing:
- `unit_<appID>_<yyyymmdd>.csv` — per-unit parameters (`UnitID, Parameter Name, Inspect, Value`).
- `unit_<appID>_<yyyymmdd>_<unitNumber>.txt` — one per calculation/logic block, containing its code; matched back to a unit ID via the `MTX####` suffix in the filename (`extract_logic_block_id`).
- `variable_<appID>_<yyyymmdd>.csv` — one row per variable, columns `Name, Type, Quantity, Initialize on reset, Copy current value to initial value at save, Keep initial value when loading program, Recipe Target, Comment, Inspect`.
- `env_<appID>_<yyyymmdd>.csv` — present but not currently parsed by `backEnd.py`.

Most UI strings, comments, and the AI prompt are in Italian; keep new user-facing strings consistent with that unless told otherwise.
