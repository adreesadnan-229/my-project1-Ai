import json
import re

import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2"

GEN_SYSTEM_PROMPT = """You are a front-end developer. You will be given a simplified description
of a Figma design (a list of elements with type, text, position/size, and colors).
Generate a SINGLE self-contained HTML file with an embedded <style> tag that recreates this design
as closely as possible using semantic HTML and CSS Flexbox/Grid.

Rules:
- The layout MUST be fully responsive (use relative units, flex-wrap, and at least one @media
  query for screens under 768px).
- Use the exact text content and colors given.
- Do not use any external libraries or frameworks, only plain HTML/CSS.
- Output ONLY the raw HTML code, starting with <!DOCTYPE html>. No explanations, no markdown fences.
"""


def _extract_html(raw):
    match = re.search(r"<!DOCTYPE html>.*", raw, re.DOTALL | re.IGNORECASE)
    return match.group(0) if match else raw.strip()


def generate_html(figma_elements):
    description = json.dumps(figma_elements, indent=2)[:6000]
    resp = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": GEN_SYSTEM_PROMPT},
                {"role": "user", "content": f"Design elements:\n{description}"},
            ],
            "stream": False,
        },
        timeout=300,
    )
    resp.raise_for_status()
    raw = resp.json()["message"]["content"]
    return _extract_html(raw)


def split_html_css(html):
    style_match = re.search(r"<style>(.*?)</style>", html, re.DOTALL)
    css = style_match.group(1).strip() if style_match else ""
    body_match = re.search(r"<body[^>]*>(.*?)</body>", html, re.DOTALL)
    body = body_match.group(1).strip() if body_match else html
    return body, css
