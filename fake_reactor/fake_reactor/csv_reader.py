import csv
import json
from pathlib import Path


class CSVReader:
    def __init__(self, filepath):
        self.filepath = filepath

    def read_lines(self):
        with open(self.filepath, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                yield row

    def to_json(self):
        for row in self.read_lines():
            yield json.dumps(row)


if __name__ == "__main__":
    print(file)
    reader = CSVReader(file)
    print([l for l in reader.to_json()])
