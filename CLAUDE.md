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

## Testing

There is a `tests/` suite (plain `unittest`, also runnable under `pytest`) but **no CI wired up yet** — there is no `.github/workflows/`. The tests come in two very different kinds; know which is which before trusting a green run:

- **Real AI integration tests** (`tests/test_ai_functionality.py`, plus `TestAICorrectionFunctionality` in `tests/test_core_functions.py`) — the meaningful ones. Each discovers *every* `.gguf` under `models/` via `modelSelector.list_available_models` (exactly as `AIPanel` does), then `load_model()` + runs real `AICorrection` inference on each; nothing about `llama_cpp` is mocked. They `self.skipTest(...)` cleanly when `models/` has no GGUF (the models aren't versioned), so they no-op on a fresh clone or on CI without the model files. Per project convention, AI tests must exercise the real models this way — never a mock or single hardcoded model.
- **Placeholder backend tests** (`TestTextProcessingLogic` in `test_core_functions.py`, and all of `test_backend_functionality.py`) — these call `backEnd.compare_texts(...)`, **a function that does not exist**; every call raises and the surrounding `try/except` falls through to asserting on hardcoded mock dicts, so they pass without touching real code. Treat them as stubs, not coverage. Real backend tests should target functions that actually exist (`build_comparison`, `compare_units`, `compare_env`, `compare_unit_txt`, …) against the sample reports in `BasicTestEnvironment/` (gitignored fixture folders `report0000`–`report0006`).

Run the suite via the unittest runner (it `sys.exit`s non-zero on failure, so it's CI-ready):

```bash
python tests/run_all_tests.py
```

Caveats: `run_all_tests.py` only registers `test_core_functions`, `test_ai_functionality`, and `test_backend_functionality` — `tests/test_main_flow.py` and `tests/test_comprehensive.py` (the latter is an empty stub) are **not** wired into it, though `pytest` (`cd tests && pytest -v`) will discover them. `tests/testAI.py` is a standalone manual smoke script (not a `unittest` case): it hardcodes the 7B model path, calls `load_model(...)` then `AICorrection`, and prints the result — `python tests/testAI.py`, fails fast if that GGUF is absent. Test-only deps (`pytest`, `coverage`, `mock`) live in `tests/requirements_test.txt`.

## Building the portable executable

`build_portable.bat` runs PyInstaller (using `KCompareAgent.spec`-equivalent flags: `--onedir --windowed --collect-all llama_cpp`), then creates an empty `dist/KCompareAgent/models/` folder and copies `models/LEGGIMI.txt` into it — no `.gguf` model files are bundled, deliberately, to keep the portable package small (~150-250MB) and fast to distribute. End users copy whichever GGUF model(s) they want into that folder themselves; `AIPanel`'s "no models found" state (see below) handles the empty-folder case gracefully on first run. The script finishes by zipping the whole `dist/KCompareAgent` folder into `dist/KCompareAgent.zip` via PowerShell `Compress-Archive`, so distribution is a single file — extract and run `KCompareAgent.exe`, no installer, no admin rights needed.

The `.venv` this is built from currently has GPU/CUDA support compiled into `llama_cpp_python` (`ggml-cuda.dll` alongside `ggml-cpu.dll`) — portability of that CUDA backend onto a machine without an NVIDIA GPU/driver has not been verified yet at the time of writing; test the packaged exe on such a machine before relying on it.

`build/` and `dist/` are gitignored output directories; `.gguf` model files are gitignored too (they're large binaries, must be obtained/placed manually under `models/`) — `models/LEGGIMI.txt` is the one tracked exception, documenting which filenames `MODEL_CATALOG` (`src/modelSelector.py`) recognizes for friendly display names.

## Architecture

The app follows a strict front-end/back-end split, wired together only in `Main.py`. The UI itself is a `src/gui/` package (split out of a single 900-line `frontEnd.py` for maintainability — see breakdown below).

- **`src/backEnd.py`** — pure, UI-free logic. No Tkinter imports. Responsible for:
  - Locating and parsing report folder contents (`unit_*.csv`, `variable_*.csv`, `unit_*.txt`, `env_*.csv`) via `load_report`.
  - Diffing two parsed reports: `compare_units`, `compare_variables`, `compare_unit_txt` (line-level diff of logic-block `.txt` files using `difflib.SequenceMatcher`), `compare_env` (controller config registers, keyed by register path, comparing `description`/`value`).
  - Rendering diff results to Markdown (`render_units_changes`, `render_variables_changes`, `render_logic_changes`, `render_env_changes`).
  - `build_comparison(report_a_path, report_b_path)` — loads and diffs both report folders, returning the structured diff data (`title_a`, `title_b`, `units`, `variables`, `logic`, `env`, `env_title_a`, `env_title_b`) undecorated by any rendering. This is the single source of truth for diff data; both `build_preview` (Markdown) and `src/gui/diff_tree.py`'s `DiffTree` (Treeview) consume it independently rather than one another.
  - Top-level orchestration: `generate_changelog` (writes `ChangeLog_<A>_<B>.md` to disk) and `build_preview` (calls `build_comparison` then renders the same diff to a Markdown string for in-app use, no file write).
  - `validate_report_folder` checks a folder has the required `unit_*.csv` / `variable_*.csv` files before it's accepted in the UI.
  - `get_version` reads the application version out of a `variable_*.csv`'s `#Version`/`#Versione` row.
  - `append_change_record` appends a `[folder, version, comment]` row to a `Changes_*.csv` log (`;`-delimited), writing a header on first write and fixing a missing trailing newline before appending.
  - `render_units_changes`'s REMOVED- section destructures `(unit_id, unit_name)` tuples directly when iterating `unit_cmp["removed_units"]`. It used to do a `unit_cmp.get(unit_id, {})` lookup against `unit_id` as if it were a dict key (it's actually the tuple itself), which always missed and printed the raw tuple repr in generated changelogs instead of the unit name — fixed; don't reintroduce the lookup pattern.
  - `load_last_paths`/`save_last_paths` persist the last-used Report A / Report B / output folder paths to `%APPDATA%\KCompareAgent\last_paths.json` (falls back to `~` if `APPDATA` is unset), so `InputPage` can default to them on next launch. `load_last_paths` returns empty-string defaults if the file is missing or corrupt — never raises.
  - `list_autocomplete_terms(folder)` collects whole-field candidate names (unit IDs, unit names, a combined `"U<Num> <unit name>"` form per unit, variable names, logic-block IDs/names) from a parsed report, for use as the Tab-completion dictionary in `PreviewPage`'s comment box. Names are taken whole (a full CSV field/line), never split on spaces, since report names legitimately contain spaces.

- **`src/gui/`** — the UI, split by responsibility:
  - **`app.py`** — `CompareApp(tk.Tk)`, the shell. Owns the two pages (`InputPage`, `PreviewPage`) and switches between them with `pack`/`pack_forget` (no multi-window flow). All business logic (`validate_fn`, `generate_fn`, `preview_fn`, `compare_fn`, `get_version`, `load_paths_fn`, `save_paths_fn`) is dependency-injected here from `Main.py` rather than imported directly inside the pages — keep that separation when extending the UI.
  - **`page_input.py`** — `InputPage`: pick Report A folder, Report B folder, output folder; live-validates via the injected `validate_fn` and enables "Next" only when both report folders pass validation. On init, populates the three fields from the injected `load_paths_fn` (`backEnd.load_last_paths`); on a successful "Next", calls `save_paths_fn` (`backEnd.save_last_paths`) before handing control to `on_next(report_a, report_b, output_dir)` — so defaults reflect the last paths actually used for a comparison, not abandoned in-progress edits.
  - **`page_preview.py`** — `PreviewPage`: on `load_preview`, calls both the injected `preview_fn` (Markdown string, used as the AI panel's "auto" input) and `compare_fn` (structured diff data, fed into `DiffTree.load_comparison`); also collects `backEnd.list_autocomplete_terms` for both report folders into `self.autocomplete_terms`. Also hosts the "Comment" box, the `AIPanel`, "Generate Log" (`generate_fn`) and "Update Changes_*.csv" (`backEnd.append_change_record`). The comment box's `<Tab>` is bound to `_on_comment_tab`: it scans every suffix of the already-typed text on the current line (longest first) for the first one that's a case-insensitive prefix of a known term, then completes to it; repeated Tab presses at the same cursor position cycle through all matches. This works anywhere in the line (not just at line start) — an earlier version matched only the whole line-start-to-cursor text and broke for any text preceding the candidate name.
  - **`diff_tree.py`** — `DiffTree(ttk.Treeview)`: native, expandable/collapsible hierarchical view of a comparison (Units/Variables/Logic blocks/Environment → ADDED+/REMOVED-/MODIFIED → details), built directly from `backEnd.build_comparison`'s structured data rather than from rendered Markdown/HTML. Environment is always the last section (`_add_env_section`). Replaced the old HTML preview (`tkinterweb.HtmlFrame`) to get native VS-Code/Visual-Studio-style expand/collapse, which the Tkhtml-based HTML engine couldn't support (no HTML5 `<details>`/CSS3 sibling-combinator support, no real JS execution).
  - **`ai_panel.py`** — `AIPanel`: the AI-assisted correction widget. Imports `AICorrection`, `MODELS_DIR`, `load_model` directly from `src/AICorrector.py`, and `detect_hardware`/`list_available_models`/`recommend_model` from `src/modelSelector.py` (not injected, same exception to DI as before). A `ttk.Combobox` to the left of the "Correct" button lists every model found under `models/` (via `list_available_models`), labeled with friendly display names; on panel build it defaults to `recommend_model`'s pick for the detected hardware and loads it. Both the initial load and any later reload (triggered by `<<ComboboxSelected>>` via `on_model_change`) run in a background `threading.Thread` calling `AICorrector.load_model(path)`, with the combo and "Correct" button disabled for the duration and re-enabled via `self.after(...)` on success/error — reusing the same threading pattern as the correction call itself (also disabled together during a correction, so a model can't be swapped mid-inference). The correction call runs in a background `threading.Thread` and marshals results back to the UI via `self.after(...)`, since `llama-cpp-python` inference is slow and must not block the Tk mainloop.
  - **`theme.py`** — shared colors/fonts constants.

- **`src/modelSelector.py`** — hardware detection and model selection, no `llama_cpp` dependency (cheap to import). `detect_hardware()` returns CPU core count (`os.cpu_count()`), total RAM in GB (via `ctypes.windll.kernel32.GlobalMemoryStatusEx`, Windows-only), and NVIDIA GPU name/VRAM in GB if present (via a `nvidia-smi --query-gpu=... --format=csv,noheader` subprocess call, gracefully `None`/`None` if `nvidia-smi` is missing or errors). `list_available_models(models_dir)` scans `models/` for `.gguf` files, grouping multi-shard models (`xxx-00001-of-0000N.gguf` convention) into a single entry keyed by the first shard's path — and only listing them if *all* expected shards are present, so an incomplete download doesn't show up as selectable. Each entry is matched by filename against `MODEL_CATALOG` (a hardcoded list of known models with `display_name`/`tier`/`min_ram_gb`/`min_vram_gb`); files not in the catalog still get listed (tier `"unknown"`, `display_name` = filename) so any model dropped into the folder is selectable even without curated metadata. `recommend_model(available_models, hardware)` picks `"heavy"` tier if VRAM ≥ 6GB, else `"medium"` if VRAM ≥ 3GB or RAM ≥ 16GB, else `"light"`, falling back down the tiers (and finally to the smallest available model) if the preferred tier isn't present. Current `MODEL_CATALOG`: `Qwen3-1.7B-Q4_K_M.gguf` (light, CPU), `Qwen2.5-3B-Instruct-Q4_K_M.gguf` (medium, CPU/GPU), and `qwen2.5-7b-instruct-q5_k_m-00001-of-00002.gguf` (heavy, GPU recommended). Heads-up: `models/` currently holds a *different* 3B build — `qwen2.5-3b-instruct-fp16-00001-of-00002.gguf` (fp16, 2 shards) — whose filename doesn't match the catalog's `Q4_K_M` medium entry, so it lists as tier `"unknown"` (display name = filename) rather than as the curated medium tier, and the medium catalog entry has no matching file on disk. To have it recommended by tier, either add its exact filename to `MODEL_CATALOG` or drop the `Q4_K_M` build into `models/`.

- **`src/AICorrector.py`** — no longer loads a model at import time, and no longer hardcodes a single `MODEL_PATH`. `MODELS_DIR` (what `modelSelector.list_available_models` and `ai_panel.py` scan) resolves relative to the executable directory when frozen (PyInstaller) vs. relative to the source tree otherwise — `Path(sys.executable).parent` vs `Path(__file__).resolve().parent.parent`. The module-level `llm` starts as `None`; `load_model(model_path)` instantiates `Llama` and assigns it to `llm`, choosing GPU params (`n_gpu_layers=-1`, `n_ctx=4096`) if `modelSelector.detect_hardware()` reports any VRAM, else CPU-only params (`n_ctx=32768`) — this replaces the old hardcoded `GPU_Nvidia` flag. `load_model` can be called again later to hot-swap models (used by `ai_panel.py`'s dropdown); it `llm.close()`s the previous instance before loading the next and records the path, which `get_current_model_path()` returns (the AI tests use it to assert which model is live). `AICorrection(auto, human)` raises `RuntimeError` if called before any `load_model` call; otherwise it sends the auto-generated Markdown diff and the human comment as a single user message (`//AUTO\n...\n//HUMAN\n...`) using a system prompt from `src/promptCorrettore.txt`, and returns the model's `//Correzione:` / `//Suggerimento:` formatted reply (any `<think>...</think>` block is stripped). Because `AICorrector.py` still imports `llama_cpp` at module level (just no longer loads a model eagerly), anything importing `src/gui/ai_panel.py` (and transitively `src/gui/page_preview.py` / `src/gui/app.py`) still requires `llama_cpp` to be installed/importable — keep that in mind if writing tests that only need `theme.py`, `diff_tree.py`, `page_input.py`, or `modelSelector.py`, which have no AI dependency and import cheaply.

- **`docs/generateChangeLog.txt`** is the spec for the report folder format and changelog content/structure (file naming conventions, CSV column layouts for `unit_*.csv`, `variable_*.csv` and `env_*.csv`, what ADDED+/REMOVED-/MODIFIED sections must contain). Treat it as the source of truth when changing diff/parsing logic in `backEnd.py`.
  - `docs/GenerateChangeLog.spec` references a `GenerateChangeLog.py` entry point that doesn't currently exist in the repo — it appears to be a leftover/older PyInstaller spec, not the one actually used (`KCompareAgent.spec` at the repo root targets `Main.py` and is the live one referenced by `build_portable.bat`).

## Domain notes (Keyence report folders)

A "report" is a folder named `report<id>` containing:
- `unit_<appID>_<yyyymmdd>.csv` — per-unit parameters (`UnitID, Parameter Name, Inspect, Value`).
- `unit_<appID>_<yyyymmdd>_<unitNumber>.txt` — one per calculation/logic block, containing its code; matched back to a unit ID via the `MTX####` suffix in the filename (`extract_logic_block_id`).
- `variable_<appID>_<yyyymmdd>.csv` — one row per variable, columns `Name, Type, Quantity, Initialize on reset, Copy current value to initial value at save, Keep initial value when loading program, Recipe Target, Comment, Inspect`.
- `env_<appID>_<yyyymmdd>.csv` — snapshot of the controller's configuration registers (camera config, lighting params, hardware/controller settings, scaling/compensations). First row is `,Env,<title>`; every following row is a register `<RegisterKey>,"<description>","<value>",`. Parsed and compared by `backEnd.py` (`parse_env_csv`/`compare_env`/`render_env_changes`) the same way as `unit_*.csv`/`variable_*.csv`, shown as the final "Environment" section in both the changelog Markdown and `DiffTree`.

Most UI strings, comments, and the AI prompt are in Italian; keep new user-facing strings consistent with that unless told otherwise.
