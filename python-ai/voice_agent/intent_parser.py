import json

import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2"

CELEBRATION_KEYWORDS = (
    "birthday", "eid", "anniversary", "congratulations", "wedding",
    "greeting", "card",
)

INTENT_SYSTEM_PROMPT = """You classify spoken commands for a voice assistant that can build websites,
open websites/apps, search the web, open local folders/drives, download things, and chat normally.

Output ONLY a JSON object with these fields:
{
  "action": "build_site" or "open_site" or "web_search" or "open_folder" or "download" or "create_document" or "chat",
  "platform": "wordpress" or "shopify" or "html" or null,
  "needs_figma": true or false,
  "site": string or null,
  "query": string or null,
  "target": string or null,
  "url": string or null,
  "doc_type": "excel" or "word" or "powerpoint" or "banner" or "card" or null,
  "topic": string or null
}

Rules:
- action = "build_site": user wants a website, store, or theme built/generated/made.
  platform = whichever platform they mentioned (wordpress, shopify, or plain html/website), else null.
  needs_figma = true if they reference a design, mockup, or Figma file to build from.
- action = "open_site": user wants to open a specific WEBSITE or web app with NO particular content
  mentioned (e.g. "open youtube", "open google", "open chatgpt", "open facebook"). site = the name
  they mentioned, lowercase (e.g. "youtube", "chatgpt").
- action = "web_search": user wants to find/play/watch/search for SPECIFIC content online - a song,
  video, topic, query, etc. This applies even if they also say "open" (e.g. "open youtube and play
  a pakistani song", "open youtube and search some naats", "play a song on youtube", "search cats on
  google", "google how to bake a cake"). site = which site to search on (default "google" if not
  mentioned, "youtube" if they mention playing/watching a video or song). query = what they want to
  find/play/search for.
  IMPORTANT: if any specific content (song, video, topic, search term) is mentioned, always use
  "web_search", never "open_site" - even if the word "open" appears in the sentence.
- action = "open_folder": user wants to open a folder or drive on their own computer (NOT a website) -
  e.g. "open my downloads folder", "open D drive", "open the project folder", "open drive E".
  target = the folder/drive name they mentioned, lowercase (e.g. "downloads", "d drive", "project").
- action = "download": user wants to download/save a video, song, or file (e.g. "download this
  pakistani song", "download that naat", "download this video from this link"). query = what to
  search for and download from YouTube (song/video name), if no link was given. url = a direct
  http/https link, if one was mentioned/pasted, else null.
- action = "create_document": user wants an Excel sheet, Word document/post, PowerPoint
  presentation, a banner/graphic image, or a greeting/celebration card created (e.g. "make an excel
  sheet of my expenses", "write a word post about dogs", "make a powerpoint about our product",
  "make a birthday banner", "make a beautiful birthday card", "make an eid greeting card").
  doc_type = "excel" for spreadsheets, "word" for documents/posts/articles, "powerpoint" for
  business presentations/slides (reports, sales, work topics), "banner" for a single graphic/poster
  image, "card" for a celebratory/greeting card or post.
  CRITICAL: whenever an occasion or celebration word appears (birthday, eid, anniversary,
  congratulations, wedding, greeting, "beautiful", "card") ALWAYS use doc_type "card" -
  this overrides "powerpoint"/"post" even if those words are ALSO said in the same sentence.
  "powerpoint" only applies to plain business/work/report content with no celebration involved.
  topic = what it should be about (e.g. "Happy Birthday Ahmed"), or for banner/card the exact
  occasion/text.
- action = "chat": anything else - questions, conversation, unclear requests. Note: "ChatGPT" is the
  name of a website/app, not a request to chat - "open chatgpt" is action "open_site" with
  site "chatgpt", NOT action "chat".
- Only fill platform/needs_figma for "build_site". Only fill site/query for "open_site"/"web_search".
  Only fill target for "open_folder". Only fill query/url for "download". Only fill doc_type/topic
  for "create_document". Use null for fields that don't apply.

Examples:
"open chatgpt" -> {"action": "open_site", "platform": null, "needs_figma": false, "site": "chatgpt", "query": null, "target": null, "url": null, "doc_type": null, "topic": null}
"open netflix" -> {"action": "open_site", "platform": null, "needs_figma": false, "site": "netflix", "query": null, "target": null, "url": null, "doc_type": null, "topic": null}
"open my downloads folder" -> {"action": "open_folder", "platform": null, "needs_figma": false, "site": null, "query": null, "target": "downloads", "url": null, "doc_type": null, "topic": null}
"download this pakistani naat" -> {"action": "download", "platform": null, "needs_figma": false, "site": null, "query": "pakistani naat", "target": null, "url": null, "doc_type": null, "topic": null}
"make a birthday banner" -> {"action": "create_document", "platform": null, "needs_figma": false, "site": null, "query": null, "target": null, "url": null, "doc_type": "banner", "topic": "Happy Birthday"}
"make an excel sheet for my monthly budget" -> {"action": "create_document", "platform": null, "needs_figma": false, "site": null, "query": null, "target": null, "url": null, "doc_type": "excel", "topic": "monthly budget"}
"make me a beautiful birthday card in powerpoint" -> {"action": "create_document", "platform": null, "needs_figma": false, "site": null, "query": null, "target": null, "url": null, "doc_type": "card", "topic": "Happy Birthday"}

Respond with ONLY the JSON object, no explanations.
"""


def parse_intent(text):
    resp = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            "format": "json",
            "stream": False,
            "options": {"temperature": 0},
        },
        timeout=60,
    )
    resp.raise_for_status()
    raw = resp.json()["message"]["content"]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {}

    data.setdefault("action", "chat")
    data.setdefault("platform", None)
    data.setdefault("needs_figma", False)
    data.setdefault("site", None)
    data.setdefault("query", None)
    data.setdefault("target", None)
    data.setdefault("url", None)
    data.setdefault("doc_type", None)
    data.setdefault("topic", None)

    valid_actions = ("build_site", "open_site", "web_search", "open_folder", "download", "create_document", "chat")
    if data["action"] not in valid_actions:
        data["action"] = "chat"
    if data["doc_type"] not in ("excel", "word", "powerpoint", "banner", "card", None):
        data["doc_type"] = None
    if data["platform"] not in ("wordpress", "shopify", "html", None):
        data["platform"] = None

    if data["action"] == "create_document" and any(kw in text.lower() for kw in CELEBRATION_KEYWORDS):
        data["doc_type"] = "card"

    return data


if __name__ == "__main__":
    tests = [
        "Look at my Figma design and build me a WordPress site",
        "Build this as a Shopify store from the Figma file",
        "Can you just make me a simple html landing page",
        "What's the weather like today",
        "build a site for me",
        "open youtube",
        "open google for me",
        "search cats on youtube",
        "google how to make pasta",
        "can you search funny cat videos",
    ]
    for t in tests:
        print(t, "->", parse_intent(t))
