from tkinter import ttk

from . import theme


class DiffTree(ttk.Treeview):
    """Vista gerarchica espandibile/collassabile (stile Visual Studio) di un
    confronto fra due report, costruita direttamente dai dati strutturati
    restituiti da backEnd.build_comparison (non dal Markdown renderizzato).
    """

    def __init__(self, parent):
        style = ttk.Style(parent)
        style.configure(
            "DiffTree.Treeview",
            background=theme.CARD,
            fieldbackground=theme.CARD,
            foreground=theme.TEXT,
            font=theme.FONT_NORMAL,
            rowheight=33,
            borderwidth=0
        )
        style.map(
            "DiffTree.Treeview",
            background=[("selected", theme.ACCENT)],
            foreground=[("selected", "#ffffff")]
        )

        super().__init__(parent, show="tree", selectmode="browse", style="DiffTree.Treeview")

        self.tag_configure("section", font=theme.FONT_LABEL)
        self.tag_configure("added", foreground=theme.SUCCESS)
        self.tag_configure("removed", foreground=theme.DANGER)
        self.tag_configure("modified", foreground=theme.WARNING)
        self.tag_configure("muted", foreground=theme.MUTED)

    def show_placeholder(self, text):
        self.delete(*self.get_children())
        self.insert("", "end", text=text, tags=("muted",))

    def load_comparison(self, comparison):
        self.delete(*self.get_children())

        title_a = comparison.get("title_a", "")
        title_b = comparison.get("title_b", "")
        if title_a != title_b:
            self.insert(
                "", "end",
                text=f'Inspection title: "{title_a}" -> "{title_b}"',
                tags=("modified",)
            )

        self._add_units_section(comparison["units"])
        self._add_variables_section(comparison["variables"])
        self._add_logic_section(comparison["logic"])
        self._add_env_section(
            comparison["env"],
            comparison.get("env_title_a", ""),
            comparison.get("env_title_b", "")
        )

    # ============================================================
    # UNITS
    # ============================================================
    def _add_units_section(self, unit_cmp):
        root = self.insert("", "end", text="Units", open=True, tags=("section",))

        if unit_cmp["added_units"]:
            added = self.insert(root, "end", text=f"ADDED+ ({len(unit_cmp['added_units'])})", tags=("added",))
            for uid, name in unit_cmp["added_units"]:
                self.insert(added, "end", text=f"{uid} {name}".strip(), tags=("added",))

        if unit_cmp["removed_units"]:
            removed = self.insert(root, "end", text=f"REMOVED- ({len(unit_cmp['removed_units'])})", tags=("removed",))
            for uid, name in unit_cmp["removed_units"]:
                self.insert(removed, "end", text=f"{uid} {name}".strip(), tags=("removed",))

        if unit_cmp["modified_units"]:
            modified = self.insert(root, "end", text=f"MODIFIED ({len(unit_cmp['modified_units'])})", tags=("modified",))
            for unit_id, unit_name, ch in unit_cmp["modified_units"]:
                unit_node = self.insert(modified, "end", text=f"{unit_id} {unit_name}".strip(), tags=("modified",))

                if ch["added_params"]:
                    sub = self.insert(unit_node, "end", text="added params", tags=("added",))
                    for p in ch["added_params"]:
                        self.insert(sub, "end", text=p, tags=("added",))

                if ch["removed_params"]:
                    sub = self.insert(unit_node, "end", text="removed params", tags=("removed",))
                    for p in ch["removed_params"]:
                        self.insert(sub, "end", text=p, tags=("removed",))

                if ch["modified_params"]:
                    sub = self.insert(unit_node, "end", text="modified params", tags=("modified",))
                    for p, field_changes in ch["modified_params"]:
                        p_node = self.insert(sub, "end", text=p, tags=("modified",))
                        for field, (old, new) in field_changes.items():
                            self.insert(p_node, "end", text=f'{field}: "{old}" -> "{new}"', tags=("muted",))

    # ============================================================
    # VARIABLES
    # ============================================================
    def _add_variables_section(self, var_cmp):
        root = self.insert("", "end", text="Variables", open=True, tags=("section",))

        if var_cmp["added"]:
            added = self.insert(root, "end", text=f"ADDED+ ({len(var_cmp['added'])})", tags=("added",))
            for name in var_cmp["added"]:
                self.insert(added, "end", text=name, tags=("added",))

        if var_cmp["removed"]:
            removed = self.insert(root, "end", text=f"REMOVED- ({len(var_cmp['removed'])})", tags=("removed",))
            for name in var_cmp["removed"]:
                self.insert(removed, "end", text=name, tags=("removed",))

        if var_cmp["modified"]:
            modified = self.insert(root, "end", text=f"MODIFIED ({len(var_cmp['modified'])})", tags=("modified",))
            for name, changes in var_cmp["modified"]:
                name_node = self.insert(modified, "end", text=name, tags=("modified",))
                for col, (old, new) in changes.items():
                    self.insert(name_node, "end", text=f'{col}: "{old}" -> "{new}"', tags=("muted",))

    # ============================================================
    # LOGIC BLOCKS
    # ============================================================
    def _add_logic_section(self, txt_cmp):
        root = self.insert("", "end", text="Logic blocks", open=True, tags=("section",))

        if txt_cmp["added"]:
            added = self.insert(root, "end", text=f"ADDED+ ({len(txt_cmp['added'])})", tags=("added",))
            for block_id in txt_cmp["added"]:
                self.insert(added, "end", text=block_id, tags=("added",))

        if txt_cmp["removed"]:
            removed = self.insert(root, "end", text=f"REMOVED- ({len(txt_cmp['removed'])})", tags=("removed",))
            for block_id in txt_cmp["removed"]:
                self.insert(removed, "end", text=block_id, tags=("removed",))

        if txt_cmp["modified"]:
            modified = self.insert(root, "end", text=f"MODIFIED ({len(txt_cmp['modified'])})", tags=("modified",))
            for item in txt_cmp["modified"]:
                block_node = self.insert(
                    modified, "end",
                    text=f"{item['block_id']} {item['name']}".strip(),
                    tags=("modified",)
                )

                if not item["diffs"]:
                    self.insert(block_node, "end", text="content changed, no line-level diff detected", tags=("muted",))
                    continue

                for d in item["diffs"]:
                    diff_node = self.insert(block_node, "end", text=self._format_diff_label(d), tags=("modified",))

                    if d["old_lines"]:
                        old_node = self.insert(diff_node, "end", text="OLD", tags=("removed",))
                        for line in d["old_lines"]:
                            self.insert(old_node, "end", text=line, tags=("removed",))

                    if d["new_lines"]:
                        new_node = self.insert(diff_node, "end", text="NEW", tags=("added",))
                        for line in d["new_lines"]:
                            self.insert(new_node, "end", text=line, tags=("added",))

    # ============================================================
    # ENVIRONMENT
    # ============================================================
    def _add_env_section(self, env_cmp, title_a="", title_b=""):
        root = self.insert("", "end", text="Environment", open=True, tags=("section",))

        if title_a != title_b:
            self.insert(root, "end", text=f'Title: "{title_a}" -> "{title_b}"', tags=("modified",))

        if env_cmp["added"]:
            added = self.insert(root, "end", text=f"ADDED+ ({len(env_cmp['added'])})", tags=("added",))
            for key in env_cmp["added"]:
                self.insert(added, "end", text=key, tags=("added",))

        if env_cmp["removed"]:
            removed = self.insert(root, "end", text=f"REMOVED- ({len(env_cmp['removed'])})", tags=("removed",))
            for key in env_cmp["removed"]:
                self.insert(removed, "end", text=key, tags=("removed",))

        if env_cmp["modified"]:
            modified = self.insert(root, "end", text=f"MODIFIED ({len(env_cmp['modified'])})", tags=("modified",))
            for key, changes in env_cmp["modified"]:
                key_node = self.insert(modified, "end", text=key, tags=("modified",))
                for field, (old, new) in changes.items():
                    self.insert(key_node, "end", text=f'{field}: "{old}" -> "{new}"', tags=("muted",))

    @staticmethod
    def _format_diff_label(d):
        tag = d["type"]
        old_start, old_end = d["old_line_start"], d["old_line_end"]
        new_start, new_end = d["new_line_start"], d["new_line_end"]

        if tag == "replace":
            return f"replace: old lines {old_start}-{old_end} -> new lines {new_start}-{new_end}"
        if tag == "delete":
            return f"delete: old lines {old_start}-{old_end} removed"
        if tag == "insert":
            return f"insert: new lines {new_start}-{new_end} added"
        return f"{tag}: old {old_start}-{old_end} / new {new_start}-{new_end}"
