import os


def get_next_episode_number(season_path):
    """Count existing episodes to find the next episode number."""
    existing = [
        f
        for f in os.listdir(season_path)
        if os.path.isfile(os.path.join(season_path, f))
    ]
    return len(existing) + 1


def generate_new_filename(original_filename, rule, season, episode):
    name, ext = os.path.splitext(original_filename)
    fmt = rule.get("rename_format", "{title}")
    return fmt.format(season=season, episode=episode) + ext
