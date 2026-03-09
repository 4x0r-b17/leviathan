# save_to_file.py

def save_to_file(data: dict, filename: str = "results.txt") -> None:
    with open(filename, "a") as f:
        for key, value in data.items():
            f.write(f"{key}: {value}\n")
        f.write("\n")