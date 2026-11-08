"""Prepare a GitHub README for posting on velog.

Usage:
    python readme_to_velog.py <README.md> --out <dir> [--repo owner/name] [--branch main] [--no-visibility-check]

What it does
1. Works out the GitHub repo (from --repo or the README folder's `origin` remote) and the branch.
2. Checks with `gh` that the repo is PUBLIC. Exits with code 2 if it is not (velog posts are only
   made for public repos).
3. Converts the README into velog markdown:
   - takes the first `# H1` as the post title and removes it from the body
   - rewrites relative image paths to raw.githubusercontent.com URLs
   - rewrites relative file/folder links to github.com/<repo>/blob|tree/<branch>/... URLs
   - adds a `> GitHub: <repo url>` line at the top
   - rewrites "이 저장소" (this repository) to a link to the GitHub repo
4. Writes into --out:
   - velog.md       the body markdown
   - set_body.js    a snippet for javascript_tool that puts the body into velog's CodeMirror editor
   - meta.json      {title, repo_url, images: [local image paths found in the README], body_chars}
"""
import argparse
import json
import os
import re
import subprocess
import sys


def run(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding='utf-8')
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def detect_repo(readme_dir):
    code, out, _ = run(['git', 'remote', 'get-url', 'origin'], cwd=readme_dir)
    if code != 0:
        return None
    m = re.search(r'github\.com[:/]([^/]+/[^/]+?)(?:\.git)?/?$', out)
    return m.group(1) if m else None


def detect_branch(readme_dir):
    code, out, _ = run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=readme_dir)
    return out if code == 0 and out and out != 'HEAD' else 'main'


def check_public(repo):
    code, out, err = run(['gh', 'repo', 'view', repo, '--json', 'visibility', '-q', '.visibility'])
    if code != 0:
        sys.exit(f'[error] could not read repo visibility with gh: {err}')
    return out.upper()


IMG_EXT = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg')


def is_relative(url):
    return not re.match(r'^(?:[a-z][a-z0-9+.-]*:|//|#|mailto:)', url, re.I)


def convert(md, repo, branch, readme_dir):
    base = f'https://github.com/{repo}'
    raw = f'https://raw.githubusercontent.com/{repo}/{branch}'
    images = []

    lines = md.split('\n')
    title = None
    for i, ln in enumerate(lines):
        m = re.match(r'^#\s+(.+?)\s*#*\s*$', ln)
        if m:
            title = m.group(1)
            del lines[i]
            while i < len(lines) and not lines[i].strip():
                del lines[i]
            break
        if ln.strip():
            break  # first non-empty line is not an H1
    md = '\n'.join(lines)

    # protect fenced code blocks from rewriting
    blocks = []
    def stash(m):
        blocks.append(m.group(0)); return f'\x00{len(blocks)-1}\x00'
    md = re.sub(r'```.*?```', stash, md, flags=re.S)

    def fix(m):
        bang, text, url, tail = m.group(1), m.group(2), m.group(3), m.group(4) or ''
        if not is_relative(url):
            return m.group(0)
        path = url.lstrip('./').split('#')[0]
        if bang or path.lower().endswith(IMG_EXT):
            images.append(os.path.normpath(os.path.join(readme_dir, path)))
            new = f'{raw}/{path}'
        else:
            kind = 'tree' if os.path.isdir(os.path.join(readme_dir, path)) else 'blob'
            new = f'{base}/{kind}/{branch}/{path}'
        return f'{bang}[{text}]({new}{tail})'
    md = re.sub(r'(!?)\[([^\]]*)\]\(([^)\s]+)(\s+"[^"]*")?\)', fix, md)

    # <img src="relative"> tags
    def fix_img(m):
        url = m.group(2)
        if not is_relative(url):
            return m.group(0)
        path = url.lstrip('./')
        images.append(os.path.normpath(os.path.join(readme_dir, path)))
        return f'{m.group(1)}{raw}/{path}{m.group(3)}'
    md = re.sub(r'(<img[^>]*\ssrc=")([^"]+)(")', fix_img, md)

    md = re.sub(r'\x00(\d+)\x00', lambda m: blocks[int(m.group(1))], md)
    md = md.replace('이 저장소를', f'[GitHub 저장소]({base})를').replace('이 저장소', f'[GitHub 저장소]({base})')
    body = f'> GitHub: {base}\n\n' + md.lstrip('\n')
    if not body.endswith('\n'):
        body += '\n'
    return title, body, images


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('readme')
    ap.add_argument('--out', required=True)
    ap.add_argument('--repo')
    ap.add_argument('--branch')
    ap.add_argument('--no-visibility-check', action='store_true')
    a = ap.parse_args()

    readme = os.path.abspath(a.readme)
    rdir = os.path.dirname(readme)
    repo = a.repo or detect_repo(rdir)
    if not repo:
        sys.exit('[error] could not detect the GitHub repo; pass --repo owner/name')
    branch = a.branch or detect_branch(rdir)

    if not a.no_visibility_check:
        vis = check_public(repo)
        if vis != 'PUBLIC':
            print(f'[skip] {repo} is {vis}; velog posts are only made for public repos.')
            sys.exit(2)

    md = open(readme, encoding='utf-8').read().replace('\r\n', '\n')
    title, body, images = convert(md, repo, branch, rdir)

    os.makedirs(a.out, exist_ok=True)
    open(os.path.join(a.out, 'velog.md'), 'w', encoding='utf-8', newline='\n').write(body)
    js = ("(() => { const md = " + json.dumps(body, ensure_ascii=False) + ";\n"
          "const el = document.querySelector('.CodeMirror');\n"
          "if (!el || !el.CodeMirror) return 'CodeMirror editor not found';\n"
          "el.CodeMirror.setValue(md); el.CodeMirror.refresh();\n"
          "return 'body set: ' + el.CodeMirror.getValue().length + ' chars'; })()\n")
    open(os.path.join(a.out, 'set_body.js'), 'w', encoding='utf-8', newline='\n').write(js)
    meta = {'title': title, 'repo': repo, 'branch': branch, 'repo_url': f'https://github.com/{repo}',
            'images': [p for p in images if os.path.exists(p)], 'body_chars': len(body)}
    json.dump(meta, open(os.path.join(a.out, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
