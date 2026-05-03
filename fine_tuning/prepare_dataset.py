from pathlib import Path


def main() -> None:
    output = Path("fine_tuning/datasets/processed")
    output.mkdir(parents=True, exist_ok=True)
    print("Dataset preparation placeholder.")


if __name__ == "__main__":
    main()
