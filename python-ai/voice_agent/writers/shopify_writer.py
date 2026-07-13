import os
import json

from html_gen import split_html_css


def write(html, theme_name, output_root):
    """Writes a minimal valid Shopify Online Store 2.0 theme skeleton."""
    theme_dir = os.path.join(output_root, theme_name)
    for sub in ("layout", "templates", "sections", "assets", "config"):
        os.makedirs(os.path.join(theme_dir, sub), exist_ok=True)

    body, css = split_html_css(html)

    with open(os.path.join(theme_dir, "assets", "theme.css"), "w", encoding="utf-8") as f:
        f.write(css)

    theme_liquid = """<!doctype html>
<html lang="{{ request.locale.iso_code }}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{{ page_title }}</title>
  {{ content_for_header }}
  {{ 'theme.css' | asset_url | stylesheet_tag }}
</head>
<body>
  {{ content_for_layout }}
</body>
</html>
"""
    with open(os.path.join(theme_dir, "layout", "theme.liquid"), "w", encoding="utf-8") as f:
        f.write(theme_liquid)

    main_section = f"""<div class="voice-agent-site">
{body}
</div>

{{% schema %}}
{{
  "name": "Main content",
  "settings": [],
  "presets": [
    {{ "name": "Main content" }}
  ]
}}
{{% endschema %}}
"""
    with open(os.path.join(theme_dir, "sections", "main-content.liquid"), "w", encoding="utf-8") as f:
        f.write(main_section)

    index_json = {
        "sections": {"main": {"type": "main-content", "settings": {}}},
        "order": ["main"],
    }
    with open(os.path.join(theme_dir, "templates", "index.json"), "w", encoding="utf-8") as f:
        json.dump(index_json, f, indent=2)

    settings_schema = [
        {
            "name": "theme_info",
            "theme_name": theme_name,
            "theme_version": "1.0.0",
            "theme_author": "Voice Agent",
        }
    ]
    with open(os.path.join(theme_dir, "config", "settings_schema.json"), "w", encoding="utf-8") as f:
        json.dump(settings_schema, f, indent=2)

    return theme_dir


NEXT_STEPS = (
    "Zip this theme folder and upload it in your Shopify admin under "
    "Online Store, Themes, Add theme, Upload zip file."
)
