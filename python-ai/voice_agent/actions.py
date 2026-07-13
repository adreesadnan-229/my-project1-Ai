import os
import re
import string
import urllib.parse
import webbrowser

SITE_URLS = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "gmail": "https://mail.google.com",
    "whatsapp": "https://web.whatsapp.com",
    "figma": "https://www.figma.com",
    "wordpress": "https://wordpress.com",
    "shopify": "https://www.shopify.com",
    "chatgpt": "https://chatgpt.com",
    "twitter": "https://twitter.com",
    "x": "https://twitter.com",
    "linkedin": "https://www.linkedin.com",
    "github": "https://github.com",
    "netflix": "https://www.netflix.com",
    "amazon": "https://www.amazon.com",
}

SEARCH_URL_TEMPLATES = {
    "youtube": "https://www.youtube.com/results?search_query={}",
    "google": "https://www.google.com/search?q={}",
}


def open_site(site_name):
    key = (site_name or "google").strip().lower()
    url = SITE_URLS.get(key, f"https://www.{key}.com")
    webbrowser.open(url)
    return url


def web_search(query, site_name="google"):
    key = (site_name or "google").strip().lower()
    template = SEARCH_URL_TEMPLATES.get(key, SEARCH_URL_TEMPLATES["google"])
    url = template.format(urllib.parse.quote_plus(query or ""))
    webbrowser.open(url)
    return url


SPECIAL_FOLDERS = {
    "desktop": "Desktop",
    "documents": "Documents",
    "document": "Documents",
    "downloads": "Downloads",
    "download": "Downloads",
    "pictures": "Pictures",
    "photos": "Pictures",
    "videos": "Videos",
    "music": "Music",
}


def _find_drive_letter(text):
    match = re.search(r"\b([a-z])\s*(?:[:]|drive)\b", text) or re.search(r"\bdrive\s*([a-z])\b", text)
    return match.group(1).upper() if match else None


def _normalize(name):
    return re.sub(r"[\s_-]+", "", name.lower())


def _search_for_folder(name, search_roots):
    target = _normalize(name)
    for root in search_roots:
        if not os.path.isdir(root):
            continue
        try:
            entries = os.listdir(root)
        except (PermissionError, OSError):
            continue
        for entry in entries:
            full = os.path.join(root, entry)
            if os.path.isdir(full):
                entry_norm = _normalize(entry)
                if not entry_norm:
                    continue
                is_match = target == entry_norm or target in entry_norm
                # only allow "folder name is part of what was said" for names
                # long enough to not trigger on trivial short substrings
                if not is_match and len(entry_norm) >= 4 and entry_norm in target:
                    is_match = True
                if is_match:
                    return full
    return None


def open_folder(target_name):
    """Tries to open a local folder/drive matching what was said.
    Returns the path opened, or None if nothing matched."""
    text = (target_name or "").strip().lower()
    if not text:
        return None

    drive_letter = _find_drive_letter(text)
    if drive_letter:
        path = f"{drive_letter}:\\"
        if os.path.isdir(path):
            os.startfile(path)
            return path
        return None

    home = os.path.expanduser("~")
    for key, folder_name in SPECIAL_FOLDERS.items():
        if key in text:
            path = os.path.join(home, folder_name)
            if os.path.isdir(path):
                os.startfile(path)
                return path

    search_roots = [
        os.path.join(home, "Desktop"),
        os.path.join(home, "Documents"),
        os.path.join(home, "Downloads"),
        home,
    ]
    for letter in string.ascii_uppercase:
        drive_root = f"{letter}:\\"
        if os.path.isdir(drive_root):
            search_roots.append(drive_root)

    found = _search_for_folder(text, search_roots)
    if found:
        os.startfile(found)
    return found
