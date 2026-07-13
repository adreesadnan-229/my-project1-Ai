import requests

FIGMA_API = "https://api.figma.com/v1"


def get_file(file_key, token):
    headers = {"X-Figma-Token": token}
    resp = requests.get(f"{FIGMA_API}/files/{file_key}", headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()


def _walk(node, out):
    entry = {
        "name": node.get("name"),
        "type": node.get("type"),
    }
    box = node.get("absoluteBoundingBox")
    if box:
        entry["box"] = {k: box.get(k) for k in ("x", "y", "width", "height")}

    if node.get("type") == "TEXT":
        entry["text"] = node.get("characters")
        style = node.get("style", {})
        entry["fontSize"] = style.get("fontSize")
        entry["fontWeight"] = style.get("fontWeight")

    fills = node.get("fills") or []
    colors = []
    for f in fills:
        if f.get("type") == "SOLID" and "color" in f:
            c = f["color"]
            colors.append(
                "#{:02x}{:02x}{:02x}".format(
                    round(c["r"] * 255), round(c["g"] * 255), round(c["b"] * 255)
                )
            )
    if colors:
        entry["colors"] = colors

    out.append(entry)
    for child in node.get("children", []) or []:
        _walk(child, out)


def simplify_design(file_json):
    """Flatten a Figma file's document tree into a list of elements
    (name, type, position/size, text, colors) that's easy to feed to an LLM."""
    document = file_json["document"]
    elements = []
    for page in document.get("children", []):
        for frame in page.get("children", []):
            _walk(frame, elements)
    return elements


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) != 3:
        print("Usage: python figma_client.py <file_key> <token>")
        sys.exit(1)

    data = get_file(sys.argv[1], sys.argv[2])
    simplified = simplify_design(data)
    print(json.dumps(simplified, indent=2)[:3000])
