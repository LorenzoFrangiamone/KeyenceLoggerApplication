from src.frontEnd import CompareApp
from src.backEnd import validate_report_folder, generate_changelog, build_preview, get_version

def main():
    app = CompareApp(
        validate_fn=validate_report_folder,
        generate_fn=generate_changelog,
        preview_fn=build_preview,
        get_version=get_version
    )
    app.mainloop()


if __name__ == "__main__":
    main()