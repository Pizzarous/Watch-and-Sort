# Watch and Sort

A Python tool that **watches folders**, automatically **sorts**, **renames**, and **copies** files based on customizable rules. Perfect for automating media organization from RSS downloads, torrent clients, or any automated download system.

## Use Cases

**Perfect for Media Server Automation:**

- **Torrent Client**: Sort completed downloads
- **Media Server Organization**: Maintain clean, properly named media libraries
- **Automated Workflows**: Bridge the gap between download tools and media servers

**Example Workflow:**

1. RSS feed downloads new episode to `D:/downloads/complete/`
2. Watch and Sort detects the file and matches it to your rules
3. File gets copied to `S:/media/TV/Show Name/Season 1/` and renamed to `Show Name - S01E05.mkv`
4. Your media server (Plex, Jellyfin, etc.) automatically picks up the properly organized file

## Features

- **Real-time monitoring**: Watches specified folders for new files as they appear
- **Smart matching**: Matches filenames against user-defined keyword rules
- **Automatic renaming**: Uses season and episode numbering with customizable formats
- **Organized copying**: Copies matched files to structured destination folders
- **Manual rescanning**: Supports on-demand scanning of all watched folders
- **Graceful handling**: Manages incomplete or partial files safely
- **Easy configuration**: Set up rules via a simple `rules.json` file

## Getting Started

### Option 1: Use the Pre-built Executable

1. Download the latest release from the [releases tab](https://github.com/Pizzarous/Watch-and-Sort/releases)
2. Run the executable directly

> **Note**: Your antivirus might flag this as a false positive since it's packaged with PyInstaller.

### Option 2: Run from Source

1. **Clone the repository**

   ```bash
   git clone https://github.com/Pizzarous/Watch-and-Sort.git
   cd Watch-and-Sort
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your rules**

   - On first run, a sample `rules.json` will be created
   - Edit this file to define your source folders, keywords, destinations, and naming formats

4. **Run the program**
   ```bash
   python main.py
   ```

## Configuration

### Basic Example

```json
{
  "rules": [
    {
      "source": "D:/downloads/complete",
      "match_keywords": ["succession"],
      "destination": "S:/media/TV/Succession/Season 1",
      "rename_format": "Succession - S{season:02d}E{episode:02d}",
      "season": 1
    },
    {
      "source": "D:/downloads/complete",
      "match_keywords": ["the office", "S2"],
      "destination": "S:/media/TV/The Office/Season 2",
      "rename_format": "The Office - S{season:02d}E{episode:02d}",
      "season": 2
    }
  ]
}
```

### Rule Parameters

- `source`: Path to the folder to monitor
- `match_keywords`: List of keywords to match in filenames (if you put multiple, they all have to match)
- `destination`: Target folder for organized files
- `rename_format`: Template for renaming files (supports `{season}` and `{episode}` placeholders)
- `season`: Season number (defaults to 1 if not specified)

## Usage

1. Start the program - it will begin monitoring your configured folders
2. When new matching files appear, they're automatically copied and renamed
3. Press **ENTER** at any time to manually scan all watched folders
4. Use **Ctrl+C** to stop the program

## How It Works

- **Automatic episode numbering**: Files are numbered based on existing files in the destination folder
  - Example: If you have 6 files in Season 1, the next file will be named `S01E07`
- **Smart file handling**: Skips incomplete downloads and handles file conflicts gracefully
- **Non-destructive**: Original files remain in the source folder; only copies are moved

## Notes

- If a source folder doesn't exist, the program will skip it with a warning
- Season defaults to 1 if not specified in a rule
- File monitoring continues in the background until manually stopped

## Issues & Support

If you encounter any problems or have suggestions for improvements:

1. **Check existing issues** first to see if your problem has already been reported
2. **Create a new issue** on the [GitHub Issues page](https://github.com/Pizzarous/Watch-and-Sort/issues)
3. **Include the following information**:
   - Your operating system
   - Python version (if running from source)
   - Your `rules.json` configuration
   - Error messages or unexpected behavior
   - Steps to reproduce the issue

**Common Issues:**

- **Antivirus blocking the executable**: Add an exception for the program
- **Files not being detected**: Check that your source folder paths are correct
- **Permission errors**: Ensure the program has read/write access to source and destination folders

## Support the Project

If you find this tool useful and want to support its development:

[![Ko-fi](https://img.shields.io/badge/Ko--fi-Support%20Me-red.svg)](https://ko-fi.com/pizzarous)

Your support helps maintain and improve the project. Thank you! 🙏
