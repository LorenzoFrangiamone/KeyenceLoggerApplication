import os
import csv
import glob
import json
import re
from collections import defaultdict
from difflib import SequenceMatcher


# ============================================================
# UTILS GENERICI
# ============================================================

def find_first(pattern, folder):
    matches = glob.glob(os.path.join(folder, pattern))
    return matches[0] if matches else None


def find_all(pattern, folder):
    return sorted(glob.glob(os.path.join(folder, pattern)))


def read_csv_rows(path):
    rows = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            row = [c.strip() for c in row]
            if any(cell != "" for cell in row):
                rows.append(row)
    return rows


def read_text(path):
    with open(path, "r", encoding="utf-8-sig", errors="ignore") as f:
        return f.read().strip()


def normalize_value(v):
    return "" if v is None else str(v).strip()


def get_version(folder_path):
    pattern = os.path.join(folder_path, "*variable_*.csv")
    matching_files = glob.glob(pattern)

    if not matching_files:
        print("Nessun CSV con 'variable_' nel nome trovato in:", folder_path)
        return None
    
    path = matching_files[0]
    rows = read_csv_rows(path)

    keywords = {
        "#Version",
        "#Versione"
    }

    for row in rows:
        print("debug "+row[0])
        if row[0] in keywords:
            if len(row) > 8:
                return "'"+row[8].strip()
            else:
                return ""

    return ""


# ============================================================
# VALIDAZIONE CARTELLE
# ============================================================

def validate_report_folder(folder):
    """
    Ritorna:
    (is_valid, errors, warnings)
    """
    errors = []
    warnings = []

    if not folder:
        errors.append("Path vuoto.")
        return False, errors, warnings

    if not os.path.isdir(folder):
        errors.append("La cartella non esiste.")
        return False, errors, warnings

    unit_csv = find_first("unit_*.csv", folder)
    var_csv = find_first("variable_*.csv", folder)
    unit_txt = find_all("unit_*.txt", folder)
    env_csv = find_first("env_*.csv", folder)

    if not unit_csv:
        errors.append("Manca un file unit_*.csv")

    if not var_csv:
        errors.append("Manca un file variable_*.csv")

    if not unit_txt:
        warnings.append("Nessun file unit_*.txt trovato")

    if not env_csv:
        warnings.append("Nessun file env_*.csv trovato")

    return len(errors) == 0, errors, warnings


# ============================================================
# PARSER CSV / TXT
# ============================================================

def parse_unit_csv(path):
    rows = read_csv_rows(path)
    result = {"title": "", "units": defaultdict(dict)}

    if not rows:
        return result

    first = rows[0] + [""] * (4 - len(rows[0]))
    start_idx = 1 if (len(first) >= 4 and first[0] == "UnitID") else 0

    if start_idx == 1:
        result["title"] = first[3]

    for row in rows[start_idx:]:
        row = row + [""] * (4 - len(row))
        uid, param, inspect, value = row[:4]

        if not uid:
            continue

        if row[0] == row[1]:
            unit_name = row[2] if len(row) > 2 else ""
        
        if unit_name:
            result["units"][uid]["__NAME__"] = unit_name
     
        key = param if param else "__UNIT__"

        result["units"][uid][key] = {
            "inspect": inspect,
            "value": value
        }

    return {"title": result["title"], "units": dict(result["units"])}

def parse_variable_csv(path):
    rows = read_csv_rows(path)
    if not rows:
        return {}

    header = rows[0]
    data = {}

    for row in rows[1:]:
        row += [""] * (len(header) - len(row))
        record = dict(zip(header, row))
        name = record.get("Name", "").strip()
        if name:
            data[name] = record

    return data

def parse_env_csv(path):
    rows = read_csv_rows(path)
    result = {"title": "", "registers": {}}

    if not rows:
        return result

    first = rows[0]
    start_idx = 0
    if len(first) >= 2 and first[1] == "Env":
        result["title"] = first[2] if len(first) > 2 else ""
        start_idx = 1

    for row in rows[start_idx:]:
        row = row + [""] * (3 - len(row))
        key, description, value = row[:3]

        if not key:
            continue

        result["registers"][key] = {
            "description": description,
            "value": value
        }

    return result

def find_txt_unit_name(unitId, folder):
    unit_csv_path = find_first("unit_*.csv", folder)
    rows = read_csv_rows(unit_csv_path)
    
    if not rows:
        return "unit file is empty"

    first = rows[0] + [""] * (4 - len(rows[0]))
    start_idx = 1 if (len(first) >= 4 and first[0] == "UnitID") else 0

    for row in rows[start_idx:]:
        if row[0] == row[1] and row[0] == unitId:
            return row[2]
    
    return "name not found"

def extract_logic_block_id(filename):
    """
    Esempi:
      unit_0000_20260622_102624_MTX0006.txt -> U0006
      unit_0000_20260622_102302_MTX0006.txt -> U0006
    """
    base = os.path.basename(filename)
    m = re.search(r'(MTX[0-9A-Za-z]+)\.txt$', base, re.IGNORECASE)
    if m:
        return "U" + m.group(1).upper()[3:]
    return os.path.splitext(base)[0]

def parse_unit_txt_files(folder):
    txt_files = find_all("unit_*.txt", folder)
    result = {}
    for path in txt_files:
        fname = os.path.basename(path)
        block_id = extract_logic_block_id(fname)
        name = find_txt_unit_name(block_id, folder)
        result[block_id] = {
            "name": name,
            "content": read_text(path)
        }

    return result

# ============================================================
# LOAD REPORT
# ============================================================

def load_report(folder):
    report = {
        "folder": folder,
        "unit_csv": {"title": "", "units": {}},
        "variables": {},
        "unit_txt": {},
        "env_csv": {"title": "", "registers": {}}
    }

    unit_csv_path = find_first("unit_*.csv", folder)
    var_csv_path = find_first("variable_*.csv", folder)
    env_csv_path = find_first("env_*.csv", folder)

    if unit_csv_path:
        report["unit_csv"] = parse_unit_csv(unit_csv_path)

    if var_csv_path:
        report["variables"] = parse_variable_csv(var_csv_path)

    if env_csv_path:
        report["env_csv"] = parse_env_csv(env_csv_path)

    report["unit_txt"] = parse_unit_txt_files(folder)

    return report


def list_autocomplete_terms(folder):
    """
    Ritorna l'insieme dei nomi (unit ID/nome, variabili, blocchi logici)
    presenti in un report, da usare come dizionario per l'autocompletamento
    del commento. Ogni nome è preso per intero (un campo CSV/riga), non
    spezzato per spazi.
    """
    report = load_report(folder)
    terms = set()

    for uid, params in report["unit_csv"]["units"].items():
        terms.add(uid)
        name = params.get("__NAME__", "")
        if name:
            terms.add(name)
            terms.add(f"{uid} {name}")

    terms.update(report["variables"].keys())

    for block_id, entry in report["unit_txt"].items():
        terms.add(block_id)
        if entry.get("name"):
            terms.add(entry["name"])

    return terms

# ============================================================
# COMPARE
# ============================================================

def compare_units(units_a, units_b):
    out = {
        "added_units": [],
        "removed_units": [],
        "modified_units": []
    }

    unit_ids_a = set(units_a.keys())
    unit_ids_b = set(units_b.keys())

    
    out["added_units"] = [
        (uid, units_b[uid].get("__NAME__", ""))
        for uid in sorted(unit_ids_b - unit_ids_a)
    ]

    out["removed_units"] = [
        (uid, units_a[uid].get("__NAME__", ""))
        for uid in sorted(unit_ids_a - unit_ids_b)
    ]


    for unit_id in sorted(unit_ids_a & unit_ids_b):
        params_a = units_a[unit_id]
        params_b = units_b[unit_id]

        keys_a = set(params_a.keys())
        keys_b = set(params_b.keys())

        unit_changes = {
            "added_params": sorted(keys_b - keys_a),
            "removed_params": sorted(keys_a - keys_b),
            "modified_params": []
        }

        for p in sorted(k for k in (keys_a & keys_b) if k != "__NAME__"):
            a = params_a[p]
            b = params_b[p]

            field_changes = {}
            if normalize_value(a.get("inspect")) != normalize_value(b.get("inspect")):
                field_changes["inspect"] = (a.get("inspect", ""), b.get("inspect", ""))
            if normalize_value(a.get("value")) != normalize_value(b.get("value")):
                field_changes["value"] = (a.get("value", ""), b.get("value", ""))

            if field_changes:
                unit_changes["modified_params"].append((p, field_changes))

        if (
            unit_changes["added_params"]
            or unit_changes["removed_params"]
            or unit_changes["modified_params"]
        ):
            unit_name = params_a.get("__NAME__", "") or params_b.get("__NAME__", "")
            out["modified_units"].append((unit_id, unit_name, unit_changes))

    return out


def compare_variables(vars_a, vars_b):
    out = {
        "added": [],
        "removed": [],
        "modified": []
    }

    names_a = set(vars_a.keys())
    names_b = set(vars_b.keys())

    out["added"] = sorted(names_b - names_a)
    out["removed"] = sorted(names_a - names_b)

    for name in sorted(names_a & names_b):
        a = vars_a[name]
        b = vars_b[name]

        all_cols = sorted(set(a.keys()) | set(b.keys()))
        changes = {}

        for col in all_cols:
            if normalize_value(a.get(col)) != normalize_value(b.get(col)):
                changes[col] = (a.get(col, ""), b.get(col, ""))

        if changes:
            out["modified"].append((name, changes))

    return out


def compare_env(registers_a, registers_b):
    out = {
        "added": [],
        "removed": [],
        "modified": []
    }

    keys_a = set(registers_a.keys())
    keys_b = set(registers_b.keys())

    out["added"] = sorted(keys_b - keys_a)
    out["removed"] = sorted(keys_a - keys_b)

    for key in sorted(keys_a & keys_b):
        a = registers_a[key]
        b = registers_b[key]

        changes = {}
        for field in ("description", "value"):
            if normalize_value(a.get(field)) != normalize_value(b.get(field)):
                changes[field] = (a.get(field, ""), b.get(field, ""))

        if changes:
            out["modified"].append((key, changes))

    return out


# ============================================================
# DIFF RIGA-PER-RIGA FILE LOGICI
# ============================================================

def build_line_differences(old_text, new_text):
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()

    sm = SequenceMatcher(None, old_lines, new_lines)
    diffs = []

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue

        diffs.append({
            "type": tag,
            "old_line_start": i1 + 1 if (i1 < len(old_lines) or i1 > 0) else 0,
            "old_line_end": i2,
            "new_line_start": j1 + 1 if (j1 < len(new_lines) or j1 > 0) else 0,
            "new_line_end": j2,
            "old_lines": old_lines[i1:i2],
            "new_lines": new_lines[j1:j2],
        })

    return diffs


def compare_unit_txt(txt_a, txt_b):
    out = {
        "added": [],
        "removed": [],
        "modified": []
    }

    keys_a = set(txt_a.keys())
    keys_b = set(txt_b.keys())

    out["added"] = sorted(keys_b - keys_a)
    out["removed"] = sorted(keys_a - keys_b)

    for block_id in sorted(keys_a & keys_b):
        old_entry = txt_a[block_id]
        new_entry = txt_b[block_id]

        old_text = old_entry["content"]
        new_text = new_entry["content"]

        if new_entry["name"] == old_entry["name"]:
            name = new_entry["name"]
        else:
            name = f"{old_entry["name"]} ->  {new_entry["name"]}"

        if normalize_value(old_text) != normalize_value(new_text):
            diffs = build_line_differences(old_text, new_text)
            out["modified"].append({
                "block_id": block_id,
                "name": name,
                "diffs": diffs
            })

    return out


# ============================================================
# RENDER MARKDOWN
# ============================================================

def render_units_changes(unit_cmp, title_a="", title_b=""):
    lines = []
    lines.append("## Units")
    lines.append("")

    if title_a != title_b:
        lines.append(f'- Inspection title changed: "{title_a}" -> "{title_b}"')
        lines.append("")

    if unit_cmp["added_units"]:
        lines.append("### ADDED+")
        for unit_data in unit_cmp["added_units"]:
            label = f"{unit_data[0]} {unit_data[1]}"            
            lines.append(f"- {label}")

    if unit_cmp["removed_units"]:
        lines.append("")
        lines.append("### REMOVED-")
        for unit_id, unit_name in unit_cmp["removed_units"]:
            label = f"{unit_id}"
            if unit_name:
                label += f" ({unit_name})"

            lines.append(f"- {label}")

    if unit_cmp["modified_units"]:
        lines.append("")
        lines.append("### MODIFIED")
        for unit_id, unit_name, ch in unit_cmp["modified_units"]:
            label = f"{unit_id}"
            if unit_name:
                label += f" {unit_name}"

            lines.append(f"- {label}")

            if ch["added_params"]:
                lines.append("  - added params:")
                for p in ch["added_params"]:
                    lines.append(f"    - {p}")

            if ch["removed_params"]:
                lines.append("  - removed params:")
                for p in ch["removed_params"]:
                    lines.append(f"    - {p}")

            if ch["modified_params"]:
                lines.append("  - modified params:")
                for p, field_changes in ch["modified_params"]:
                    lines.append(f"    - {p}")
                    for field, (old, new) in field_changes.items():
                        lines.append(f'      - {field}: "{old}" -> "{new}"')

    return "\n".join(lines)


def render_variables_changes(var_cmp):
    lines = []
    lines.append("## Variables")
    lines.append("")

    if var_cmp["added"]:
        lines.append("### ADDED+")
        for name in var_cmp["added"]:
            lines.append(f"- '{name}'")

    if var_cmp["removed"]:
        lines.append("")
        lines.append("### REMOVED-")
        for name in var_cmp["removed"]:
            lines.append(f"- '{name}'")

    if var_cmp["modified"]:
        lines.append("")
        lines.append("### MODIFIED")
        for name, changes in var_cmp["modified"]:
            lines.append(f"- '{name}'")
            for col, (old, new) in changes.items():
                lines.append(f'  - {col}: "{old}" -> "{new}"')

    return "\n".join(lines)


def render_env_changes(env_cmp, title_a="", title_b=""):
    lines = []
    lines.append("## Environment")
    lines.append("")

    if title_a != title_b:
        lines.append(f'- Environment title changed: "{title_a}" -> "{title_b}"')
        lines.append("")

    if env_cmp["added"]:
        lines.append("### ADDED+")
        for key in env_cmp["added"]:
            lines.append(f"- {key}")

    if env_cmp["removed"]:
        lines.append("")
        lines.append("### REMOVED-")
        for key in env_cmp["removed"]:
            lines.append(f"- {key}")

    if env_cmp["modified"]:
        lines.append("")
        lines.append("### MODIFIED")
        for key, changes in env_cmp["modified"]:
            lines.append(f"- {key}")
            for field, (old, new) in changes.items():
                lines.append(f'  - {field}: "{old}" -> "{new}"')

    return "\n".join(lines)


def render_logic_changes(txt_cmp):
    lines = []
    lines.append("## Logic blocks (`unit_*.txt`)")
    lines.append("")

    if txt_cmp["added"]:
        lines.append("### ADDED+")
        for block_id in txt_cmp["added"]:
            lines.append(f"- {block_id}")

    if txt_cmp["removed"]:
        lines.append("")
        lines.append("### REMOVED-")
        for block_id in txt_cmp["removed"]:
            lines.append(f"- {block_id}")

    if txt_cmp["modified"]:
        lines.append("")
        lines.append("### MODIFIED")
        for item in txt_cmp["modified"]:
            block_id = item["block_id"]
            name = item["name"]
            diffs = item["diffs"]

            lines.append(f"- {block_id} {name}")

            if not diffs:
                lines.append("  - content changed, but no line-level diff detected")
                continue

            lines.append("  - line differences:")
            for d in diffs:
                tag = d["type"]
                old_start = d["old_line_start"]
                old_end = d["old_line_end"]
                new_start = d["new_line_start"]
                new_end = d["new_line_end"]

                if tag == "replace":
                    lines.append(
                        f"    - replace: old lines `{old_start}-{old_end}` -> new lines `{new_start}-{new_end}`"
                    )
                elif tag == "delete":
                    lines.append(
                        f"    - delete: old lines `{old_start}-{old_end}` removed"
                    )
                elif tag == "insert":
                    lines.append(
                        f"    - insert: new lines `{new_start}-{new_end}` added"
                    )
                else:
                    lines.append(
                        f"    - {tag}: old `{old_start}-{old_end}` / new `{new_start}-{new_end}`"
                    )

                if d["old_lines"]:
                    lines.append("      - OLD:")
                    for line in d["old_lines"]:
                        lines.append(f"        - `{line}`")

                if d["new_lines"]:
                    lines.append("      - NEW:")
                    for line in d["new_lines"]:
                        lines.append(f"        - `{line}`")

    return "\n".join(lines)


# ============================================================
# GENERAZIONE CHANGELOG
# ============================================================

def generate_changelog(report_a_path, report_b_path, output_dir, comment_text):
    name_a = os.path.basename(os.path.normpath(report_a_path))
    name_b = os.path.basename(os.path.normpath(report_b_path))

    output_file = os.path.join(
        output_dir,
        f"ChangeLog_{name_a}_{name_b}.md"
    )

    report_a = load_report(report_a_path)
    report_b = load_report(report_b_path)

    unit_cmp = compare_units(report_a["unit_csv"]["units"], report_b["unit_csv"]["units"])
    var_cmp = compare_variables(report_a["variables"], report_b["variables"])
    txt_cmp = compare_unit_txt(report_a["unit_txt"], report_b["unit_txt"])
    env_cmp = compare_env(report_a["env_csv"]["registers"], report_b["env_csv"]["registers"])

    parts = []
    parts.append(f"# ChangeLog__{name_a}__vs__{name_b}")
    parts.append("")
    parts.append(render_units_changes(
        unit_cmp,
        title_a=report_a["unit_csv"].get("title", ""),
        title_b=report_b["unit_csv"].get("title", "")
    ))
    parts.append("")
    parts.append(render_variables_changes(var_cmp))
    parts.append("")
    parts.append(render_logic_changes(txt_cmp))
    parts.append("")
    parts.append(render_env_changes(
        env_cmp,
        title_a=report_a["env_csv"].get("title", ""),
        title_b=report_b["env_csv"].get("title", "")
    ))
    parts.append("")
    parts.append("## Comments:")
    parts.append(comment_text.strip() if comment_text.strip() else "")

    final_text = "\n".join(parts)

    os.makedirs(output_dir, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_text)

    return output_file

def append_change_record(csv_path, folder_name, version, comment):
    """
    Aggiunge una riga [folder_name, version, comment] a csv_path (delimitatore ";").
    Scrive l'intestazione se il file è nuovo o vuoto, e si assicura che il
    file termini con un newline prima di aggiungere la riga, altrimenti
    finirebbe attaccata all'ultima riga esistente.
    """
    file_exists = os.path.exists(csv_path)
    file_is_empty = (not file_exists) or os.path.getsize(csv_path) == 0

    if file_exists and not file_is_empty:
        with open(csv_path, "rb") as check_file:
            check_file.seek(-1, os.SEEK_END)
            last_char = check_file.read(1)

        if last_char not in [b"\n", b"\r"]:
            with open(csv_path, "a", encoding="utf-8", newline="") as fix_file:
                fix_file.write("\n")

    with open(csv_path, "a", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, delimiter=";")

        if file_is_empty:
            writer.writerow(["Folder", "Version", "Comment"])

        writer.writerow([folder_name, version, comment])


def build_comparison(report_a_path, report_b_path):
    """
    Carica e confronta due cartelle report, ritornando i dati strutturati
    del diff (non renderizzati) cosi' che chi li consuma possa scegliere
    come presentarli (Markdown, albero gerarchico, ecc).
    """
    report_a = load_report(report_a_path)
    report_b = load_report(report_b_path)

    return {
        "title_a": report_a["unit_csv"].get("title", ""),
        "title_b": report_b["unit_csv"].get("title", ""),
        "units": compare_units(
            report_a["unit_csv"]["units"],
            report_b["unit_csv"]["units"]
        ),
        "variables": compare_variables(
            report_a["variables"],
            report_b["variables"]
        ),
        "logic": compare_unit_txt(
            report_a["unit_txt"],
            report_b["unit_txt"]
        ),
        "env": compare_env(
            report_a["env_csv"]["registers"],
            report_b["env_csv"]["registers"]
        ),
        "env_title_a": report_a["env_csv"].get("title", ""),
        "env_title_b": report_b["env_csv"].get("title", ""),
    }


# ============================================================
# PERSISTENZA ULTIMI PERCORSI USATI
# ============================================================

def get_last_paths_config_path():
    config_dir = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), "KCompareAgent")
    return os.path.join(config_dir, "last_paths.json")


def load_last_paths():
    """
    Ritorna gli ultimi percorsi (report_a, report_b, output_dir) usati con
    successo nell'esecuzione precedente, o stringhe vuote se non disponibili
    o se il file di configurazione è assente/corrotto.
    """
    defaults = {"report_a": "", "report_b": "", "output_dir": ""}
    config_path = get_last_paths_config_path()

    if not os.path.exists(config_path):
        return defaults

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return defaults

    defaults.update({key: data.get(key, "") for key in defaults})
    return defaults


def save_last_paths(report_a, report_b, output_dir):
    config_path = get_last_paths_config_path()
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(
            {"report_a": report_a, "report_b": report_b, "output_dir": output_dir},
            f, ensure_ascii=False, indent=2
        )


def build_preview(report_a_path, report_b_path):
    comparison = build_comparison(report_a_path, report_b_path)

    parts = []

    parts.append(render_units_changes(
        comparison["units"],
        comparison["title_a"],
        comparison["title_b"]
    ))
    parts.append("\n")
    parts.append(render_variables_changes(comparison["variables"]))
    parts.append("\n")
    parts.append(render_logic_changes(comparison["logic"]))
    parts.append("\n")
    parts.append(render_env_changes(
        comparison["env"],
        comparison["env_title_a"],
        comparison["env_title_b"]
    ))

    return "\n".join(parts)
