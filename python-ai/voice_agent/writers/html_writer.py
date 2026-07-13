import os


def write(html, theme_name, output_root):
    site_dir = os.path.join(output_root, theme_name)
    os.makedirs(site_dir, exist_ok=True)

    with open(os.path.join(site_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    return site_dir


NEXT_STEPS = "Just double-click index.html in that folder to open it in your browser."
