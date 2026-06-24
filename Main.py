from src.frontEnd import CompareApp
from src.backEnd import validate_report_folder, generate_changelog


def main():
    app = CompareApp(
        validate_fn=validate_report_folder,
        generate_fn=generate_changelog
    )
    app.mainloop()


if __name__ == "__main__":
    main()