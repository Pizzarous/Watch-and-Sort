import json
import os
import shutil
import sys
import threading
import time
from threading import Lock

from tqdm import tqdm
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


def wait_for_file_accessible(filepath, wait_time=30, retries=10):
    for _ in range(retries):
        try:
            with open(filepath, "rb"):
                return True
        except (PermissionError, IOError):
            time.sleep(wait_time)
    return False


def wait_for_file_complete(filepath, wait_time=30, retries=10):
    previous_size = -1
    for _ in range(retries):
        try:
            current_size = os.path.getsize(filepath)
        except FileNotFoundError:
            return False
        if current_size == previous_size and current_size > 0:
            return True
        previous_size = current_size
        time.sleep(wait_time)
    return False


def copy_with_progress(src, dst):
    total_size = os.path.getsize(src)
    with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
        with tqdm(
            total=total_size,
            unit="B",
            unit_scale=True,
            desc=os.path.basename(src),
            leave=True,
            bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
        ) as pbar:
            while True:
                buf = fsrc.read(1024 * 1024)  #
                if not buf:
                    break
                fdst.write(buf)
                pbar.update(len(buf))
    shutil.copystat(src, dst)


class SortHandler(FileSystemEventHandler):
    def __init__(self, rules):
        self.rules = rules
        self.processed_files = set()
        self.lock = Lock()
        self.manual_scan_in_progress = False

    def process_file(self, filepath):
        filepath = os.path.abspath(filepath)
        with self.lock:
            if filepath in self.processed_files:
                print(f"⏩ Already processed: {os.path.basename(filepath)}")
                return False
        try:
            filename = os.path.basename(filepath)

            if filename.endswith((".part", ".!qb", ".crdownload")):
                print(f"⏸️ Skipping temporary file: {filename}")
                return False

            if not wait_for_file_accessible(filepath):
                print(f"🔒 File locked or inaccessible: {filename}")
                return False

            if not wait_for_file_complete(filepath):
                print(f"⏳ File not ready yet: {filename}")
                return False

            rule = find_matching_rule(filename, self.rules)
            if rule and os.path.normpath(filepath).startswith(
                os.path.normpath(rule["source"])
            ):
                dest_folder = rule["destination"]
                os.makedirs(dest_folder, exist_ok=True)

                season_num = rule.get("season", 1)
                episode_num = get_next_episode_number(dest_folder)
                new_name = generate_new_filename(
                    filename, rule, season_num, episode_num
                )
                dest_path = os.path.join(dest_folder, new_name)

                copy_with_progress(filepath, dest_path)
                print(f"✅ Copied: {filename} → {os.path.basename(dest_path)}")
                print(f"   📁 Destination: {dest_path}\n")

                with self.lock:
                    self.processed_files.add(filepath)  # add here after success
                return True
            else:
                print(f"❌ No matching rule found: {filename}")
                return False

        except Exception as e:
            print(f"Error processing file {filepath}: {e}")
            return False

    def on_created(self, event):
        if not event.is_directory:
            try:
                with self.lock:
                    if self.manual_scan_in_progress:
                        return
                print(f"📄 New file detected: {os.path.basename(event.src_path)}")
                self.process_file(event.src_path)
            except Exception as e:
                print(f"❌ Error processing {event.src_path}: {e}")

    def on_modified(self, event):
        if not event.is_directory:
            try:
                with self.lock:
                    if self.manual_scan_in_progress:
                        return
                # Only show modification message if file isn't already processed
                filepath_abs = os.path.abspath(event.src_path)
                if filepath_abs not in self.processed_files:
                    print(f"📝 File modified: {os.path.basename(event.src_path)}")
                self.process_file(event.src_path)
            except Exception as e:
                print(f"❌ Error processing modified file {event.src_path}: {e}")


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
    handlers = {}
    watched_paths = set()

    for rule in rules:
        source = rule.get("source")
        if not source or not os.path.isdir(source):
            print(f"⚠️  Source folder does not exist or is invalid: {source}")
            continue

        if "destination" not in rule:
            print(f"⚠️  Missing 'destination' in rule: {rule}")
            continue

        if source not in handlers:
            source_rules = [r for r in rules if r.get("source") == source]
            handler = SortHandler(source_rules)
            handlers[source] = handler
            observer.schedule(handler, path=source, recursive=False)
            watched_paths.add(source)
            print(f"👀 Watching: {source}")

    observer.start()
    print(f"\n🚀 File sorter started! Monitoring {len(watched_paths)} folder(s).")

    def manual_scan():
        print("🔍 Running manual scan on all watched folders...")
        files_processed = 0
        files_skipped = 0

        # Set flag to prevent file system events during manual scan
        for handler in handlers.values():
            with handler.lock:
                handler.manual_scan_in_progress = True

        try:
            for source, handler in handlers.items():
                if not os.path.isdir(source):
                    print(f"❌ Source folder does not exist: {source}")
                    continue

                print(f"\n📂 Scanning: {source}")
                files_in_directory = os.listdir(source)
                print(f"   Found {len(files_in_directory)} items")

                for filename in files_in_directory:
                    filepath = os.path.join(source, filename)
                    if os.path.isfile(filepath):
                        print(f"   📄 {filename}")

                        # Check if already processed before attempting to process
                        filepath_abs = os.path.abspath(filepath)
                        with handler.lock:
                            if filepath_abs in handler.processed_files:
                                print(f"      ⏩ Already processed, skipping")
                                files_skipped += 1
                                continue

                        # Only process if not already processed
                        result = handler.process_file(filepath)
                        if result:
                            files_processed += 1
                        else:
                            print(f"      ❌ Skipped or failed")
                    else:
                        print(f"   📁 {filename} (directory - skipped)")

        finally:
            # Reset flag after manual scan completes
            for handler in handlers.values():
                with handler.lock:
                    handler.manual_scan_in_progress = False

        print(f"\n📊 Manual scan complete!")
        print(f"   ✅ Processed: {files_processed} files")
        print(f"   ⏩ Skipped: {files_skipped} files\n")

    def listen_for_key():
        print("\n⌨️  Press ENTER to run manual scan on all files. Ctrl+C to exit.")
        while True:
            try:
                input()
                manual_scan()
                print("👀 Resuming automatic file monitoring...")
                for path in watched_paths:
                    print(f"   📂 {path}")
                print(
                    "\n⌨️  Press ENTER to run manual scan on all files. Ctrl+C to exit."
                )
            except KeyboardInterrupt:
                print("\n👋 Stopping file sorter...")
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
