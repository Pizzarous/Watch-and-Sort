def find_matching_rule(filename, rules):
    fname_lower = filename.lower()
    for rule in rules:
        if all(keyword.lower() in fname_lower for keyword in rule["match_keywords"]):
            return rule
    return None
