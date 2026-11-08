---
name: velog-post
description: Publish a GitHub project's README as a post on the user's velog (velog.io, the account signed in to Chrome) through Claude in Chrome, with a screenshot thumbnail. Use after a project (e.g. a game Korean patch) has been pushed to GitHub, or when the user asks to post/write/upload a README or project write-up to velog ("velog에 글 써줘", "velog 올려줘", /velog-post). Only posts when the GitHub repo is PUBLIC.
---

# velog-post

Turns a pushed GitHub repo's README into a velog post, using the user's signed-in Chrome (Claude in Chrome).
Do not use Aside or any velog API/MCP for this; the user chose Claude in Chrome.

Scripts live next to this file in `scripts/`:
- `readme_to_velog.py`: visibility check + README → velog markdown + editor snippet
- `capture_file_input.js`: lets `file_upload` reach velog's thumbnail picker

## Inputs to settle first

- **README path** (local clone of the pushed repo). Make sure the latest README is committed and pushed: images are served from `raw.githubusercontent.com`, so unpushed images show as broken.
- **Thumbnail image**: a screenshot that shows the result working (for a game patch: an in-game screenshot taken while checking the patch, e.g. the translated title screen). Prefer one already in the repo (`meta.json` → `images`, first one); otherwise take/use a verification screenshot. Always set a thumbnail. Images linked in the body do NOT become velog's thumbnail automatically.
- **Tags**: 2–4 short tags from the project (e.g. `한글패치`, the game name without spaces, the engine).
- **New post or update?** If the user points at an existing post, edit it (`velog.io/write?id=<post id>`, button `수정하기`) instead of creating a duplicate.

## Step 1: prepare (stops if the repo is not public)

```bash
python -I -X utf8 "<skill dir>/scripts/readme_to_velog.py" "<repo>/README.md" --out "<scratchpad>/velog"
```

- Exit code **2** = repo is not PUBLIC → do **not** post. Tell the user the post was skipped because the repo is private.
- Prints `meta.json`: `title` (from the README's H1, removed from the body), `repo_url`, `images`, `body_chars`.
- Writes `velog.md` (body) and `set_body.js` (editor snippet). Skim `velog.md` once: links/images should all be absolute URLs.
- Post title: use the H1, adjusted to read as a post if needed (e.g. "<프로젝트> 제작 및 배포").

## Step 2: write the post in Chrome

Load the Claude in Chrome tools in one ToolSearch call (core set + `javascript_tool`, `find`, `file_upload`, `browser_batch`), call `tabs_context_mcp` (createIfEmpty), work in your own tab.

1. Navigate to `https://velog.io/write`. If it shows a login page, stop and ask the user to sign in to velog in Chrome. Never type credentials.
2. Title: click the title field (`제목을 입력하세요`) and type the title.
3. Body: run the **contents of `set_body.js`** with `javascript_tool`. Don't type the body: CodeMirror auto-indents and auto-closes brackets. Expect `body set: N chars`. Some outputs are hidden as "[BLOCKED: Cookie/query string data]" when they contain URLs; then verify with a separate call that returns only numbers, e.g. `const v=document.querySelector('.CodeMirror').CodeMirror.getValue(); [v.length, v.trim().slice(-20)]`.
4. Tags: click `태그를 입력하세요`, type each tag + Enter.
5. Screenshot and check the right-hand preview renders (headings, tables, images).

## Step 3: publish panel

1. Click `출간하기` (or `수정하기` for an existing post) at the bottom right. This only opens the panel.
2. **Thumbnail**: run `scripts/capture_file_input.js` with `javascript_tool` (expect `file input captured`). Then `find` "file input" → use its ref with `file_upload` and the screenshot's absolute path. Never click the 썸네일 업로드 button directly; that opens a native picker. Wait ~3 s and screenshot: the preview box should show the image.
3. **Summary**: velog auto-generates it from the body and mangles URLs (`https&#x3A;...`). Click the summary textarea, `ctrl+a`, type 1–2 clean Korean sentences describing the project (≤150 chars).
4. Visibility: keep `전체 공개` (public).
5. Click the final `출간하기` / `수정하기` in the panel. This publishes; the user's request to post is the approval, so don't ask again. Do ask first if anything differs from what they asked (different repo, private repo, extra posts).

## Step 4: verify and clean up

- After publishing, the tab URL becomes `https://velog.io/@<user>/<slug>`. Report this URL.
- Open `https://velog.io/@<user>/posts` (`<user>` = the handle in the published post's URL) and check the post appears at the top with the thumbnail.
- Close the tabs you opened.
- In the reply: post URL, title, tags, thumbnail used, and any README changes made for velog (absolute links etc.).

## Troubleshooting

- Publish panel coordinates move with window size; locate buttons with `find` ("출간하기 button", "수정하기 button") instead of fixed coordinates.
- If `capture_file_input.js` says the button wasn't found, the panel isn't open or the thumbnail already exists (button text `재업로드`; the script handles both).
- If the extension doesn't respond or a step fails 2–3 times, stop and tell the user what happened instead of retrying.
