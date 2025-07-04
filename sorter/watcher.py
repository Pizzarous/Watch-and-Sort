import json
import os
import shutil
import sys
import threading
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from sorter.config import load_rules
from sorter.matcher import find_matching_rule
from sorter.renamer import (
    generate_new_filename,
    get_next_episode_number,
)


def get_base_path():
    # Works both as script or bundled exe
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        )


def wait_for_file_complete(filepath, wait_time=3, retries=100):
    previous_size = -1
    for _ in range(retries):
        try:
            current_size = os.path.getsize(filepath)
        except FileNotFoundError:
            return False  # file disappeared
        if current_size == previous_size and current_size > 0:
            return True
        previous_size = current_size
        time.sleep(wait_time)
    return False


class SortHandler(FileSystemEventHandler):
    def __init__(self, rules):
        self.rules = rules

    def process_file(self, filepath):
        filename = os.path.basename(filepath)
        if filename.endswith((".part", ".!qb", ".crdownload")):
            return False

        if not wait_for_file_complete(filepath):
            print(f"File not ready yet: {filename}")
            return False

        rule = find_matching_rule(filename, self.rules)
        if rule and filepath.startswith(rule["source"]):
            dest_folder = rule["destination"]
            os.makedirs(dest_folder, exist_ok=True)

            # Use season from the rule, default to 1 if missing
            season_num = rule.get("season", 1)

            episode_num = get_next_episode_number(dest_folder)

            new_name = generate_new_filename(filename, rule, season_num, episode_num)
            dest_path = os.path.join(dest_folder, new_name)

            shutil.copy2(filepath, dest_path)
            print(f"Copied: {filename} -> {dest_path}")
            return True
        else:
            print(f"Ignored or unmatched: {filename}")
            return False

    def on_created(self, event):
        if not event.is_directory:
            self.process_file(event.src_path)


def clear_console():
    os.system("cls" if os.name == "nt" else "clear")


def process_all_existing_files(rules):
    print("Running manual scan on all watched folders...")
    for rule in rules:
        source = rule["source"]
        if not os.path.isdir(source):
            print(f"Source folder does not exist: {source}")
            continue
        for filename in os.listdir(source):
            filepath = os.path.join(source, filename)
            if os.path.isfile(filepath):
                handler = SortHandler(rules)
                handler.process_file(filepath)
    print("Manual scan complete.")


def create_example_rules(path):
    example = {
        "rules": [
            {
                "source": "D:/downloads",
                "match_keywords": ["succession"],
                "destination": "S:/media/TV/Succession",
                "rename_format": "Succession - S{season:02d}E{episode:02d}",
                "season": 1,
            },
            {
                "source": "D:/downloads/Animated",
                "match_keywords": ["arcane", "s2"],
                "destination": "S:/media/TV/Arcane",
                "rename_format": "Arcane - S{season:02d}E{episode:02d}",
                "season": 2,
            },
        ]
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(example, f, indent=2)

    print(f"\nrules.json file created at:\n  {path}")
    print("Please configure it with your own rules before running the program again.")
    input("\nPress ENTER to exit...")


def start_watching():
    base_path = get_base_path()
    config_path = os.path.join(base_path, "rules.json")

    if not os.path.isfile(config_path):
        create_example_rules(config_path)
        return

    rules = load_rules(config_path)

    if not rules:
        print(
            "Warning: No rules found in rules.json. The program will not process any files."
        )
        return

    observer = Observer()
    watched_paths = set()

    for rule in rules:
        source = rule.get("source")
        if not source or not os.path.isdir(source):
            print(f"⚠️  Source folder does not exist or is invalid: {source}")
            continue  # skip this rule

        if "destination" not in rule:
            print(f"⚠️  Missing 'destination' in rule: {rule}")
            continue

        if source not in watched_paths:
            watched_paths.add(source)
            observer.schedule(SortHandler(rules), path=source, recursive=False)
            print(f"Watching: {source}")

    observer.start()

    def listen_for_key():
        print("Press ENTER to run manual scan on all files. Ctrl+C to exit.")
        while True:
            try:
                input()
                process_all_existing_files(rules)
                time.sleep(10)  # wait a few seconds
                clear_console()
                for path in watched_paths:
                    print(f"Watching: {path}")
                print("Press ENTER to run manual scan on all files. Ctrl+C to exit.")
            except KeyboardInterrupt:
                observer.stop()
                break

    key_thread = threading.Thread(target=listen_for_key, daemon=True)
    key_thread.start()

    try:
        while observer.is_alive():
            observer.join(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
