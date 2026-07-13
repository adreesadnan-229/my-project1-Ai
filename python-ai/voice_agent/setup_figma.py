"""Run this once to save your Figma personal access token and file key.
(You type these, since reading a URL/token out loud isn't practical.)

How to get them:
- Token: figma.com -> account settings -> Personal access tokens -> Generate new token
- File key: open your Figma file in the browser, copy the part of the URL right after
  '/file/' or '/design/' (before the next slash), e.g.
  figma.com/design/ABC123XYZ/My-Design  ->  file key is ABC123XYZ
"""

import config

if __name__ == "__main__":
    token = input("Paste your Figma personal access token: ").strip()
    file_key = input("Paste your Figma file key: ").strip()
    config.save_config({"figma_token": token, "figma_file_key": file_key})
    print("Saved to config.json")
