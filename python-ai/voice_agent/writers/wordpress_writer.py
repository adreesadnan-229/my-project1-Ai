import os

from html_gen import split_html_css


def write(html, theme_name, output_root):
    theme_dir = os.path.join(output_root, theme_name)
    os.makedirs(theme_dir, exist_ok=True)

    body, css = split_html_css(html)

    style_css = f"""/*
Theme Name: {theme_name}
Author: Voice Agent
Version: 1.0
*/

{css}
"""
    with open(os.path.join(theme_dir, "style.css"), "w", encoding="utf-8") as f:
        f.write(style_css)

    index_php = f"""<?php get_header(); ?>
{body}
<?php get_footer(); ?>
"""
    with open(os.path.join(theme_dir, "index.php"), "w", encoding="utf-8") as f:
        f.write(index_php)

    header_php = """<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
  <meta charset="<?php bloginfo('charset'); ?>">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
"""
    with open(os.path.join(theme_dir, "header.php"), "w", encoding="utf-8") as f:
        f.write(header_php)

    footer_php = """<?php wp_footer(); ?>
</body>
</html>
"""
    with open(os.path.join(theme_dir, "footer.php"), "w", encoding="utf-8") as f:
        f.write(footer_php)

    functions_php = """<?php
function voice_agent_theme_assets() {
    wp_enqueue_style('voice-agent-style', get_stylesheet_uri());
}
add_action('wp_enqueue_scripts', 'voice_agent_theme_assets');
"""
    with open(os.path.join(theme_dir, "functions.php"), "w", encoding="utf-8") as f:
        f.write(functions_php)

    return theme_dir


NEXT_STEPS = "Copy this folder into your LocalWP site's wp-content/themes folder, then activate it in WordPress."
