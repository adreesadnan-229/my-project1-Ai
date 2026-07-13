import os

import html_gen
from writers import wordpress_writer, shopify_writer, html_writer

WRITERS = {
    "wordpress": wordpress_writer,
    "shopify": shopify_writer,
    "html": html_writer,
}


def generate_site(elements, platform, theme_name, output_root=None):
    if platform not in WRITERS:
        platform = "html"

    if output_root is None:
        output_root = os.path.join(os.path.dirname(__file__), "generated_sites")

    html = html_gen.generate_html(elements)
    writer = WRITERS[platform]
    out_dir = writer.write(html, theme_name, output_root)
    return out_dir, writer.NEXT_STEPS


if __name__ == "__main__":
    import sys
    import figma_client

    if len(sys.argv) != 5:
        print("Usage: python generator.py <figma_file_key> <figma_token> <theme_name> <platform:wordpress|shopify|html>")
        sys.exit(1)

    file_key, token, theme_name, platform = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    data = figma_client.get_file(file_key, token)
    elements = figma_client.simplify_design(data)
    out_dir, next_steps = generate_site(elements, platform, theme_name)
    print(f"Site written to: {out_dir}")
    print(next_steps)
