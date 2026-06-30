from src.gui.app import CompareApp
from src.backEnd import (
    validate_report_folder, generate_changelog, build_preview, build_comparison,
    get_version, load_last_paths, save_last_paths
)

def main():
    app = CompareApp(
        validate_fn=validate_report_folder,
        generate_fn=generate_changelog,
        preview_fn=build_preview,
        compare_fn=build_comparison,
        get_version=get_version,
        load_paths_fn=load_last_paths,
        save_paths_fn=save_last_paths
    )
    app.mainloop()


if __name__ == "__main__":
    main()