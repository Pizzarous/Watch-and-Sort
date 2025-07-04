import json
import os


def load_rules(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"rules.json not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            rules = data.get("rules")
            if not rules:
                print("No 'rules' found in rules.json. Please configure the file.")
                return []
            return rules
        except json.JSONDecodeError:
            print("Invalid JSON format in rules.json.")
            return []
