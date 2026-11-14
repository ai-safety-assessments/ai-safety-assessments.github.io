#!/usr/bin/env python3
"""Build the published site from the markdown in this repository.

Weekly issues are rendered through tools/build-weekly-page.py, the same builder
that produced the artifact pages, so the published issue carries the full design
(masthead, section nav, rating chips, evidence table). The builder inlines the
stylesheet; here it is stripped back out and replaced with a link to
assets/weekly.css, so the stylesheet is fetched once and cached across issues.

Anything else is rendered generically.

Usage: python3 tools/build-site.py <output-dir>
"""
import sys, pathlib, html, datetime, subprocess, tempfile, re

try:
    import markdown as md_lib
except ImportError:
    md_lib = None

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "_site")
CSS = ROOT / "assets" / "weekly.css"
WEEKLY_BUILDER = ROOT / "tools" / "build-weekly-page.py"
SHELL = (ROOT / "tools" / "page-shell.html").read_text(encoding="utf-8")
SITE = "https://ai-safety-assessments.github.io/"
DESCRIPTION = "Evidence-graded assessment of AI safety developments."
SECTIONS = ["reports", "baseline", "register"]


def page(title, body, root, canonical, description=DESCRIPTION):
    # Plain substitution, not str.format: the shell carries JavaScript, and
    # every brace in it would otherwise have to be escaped.
    out = SHELL
    for key, value in (("title", html.escape(title)), ("root", root),
                       ("canonical", canonical),
                       ("description", html.escape(description)), ("body", body)):
        out = out.replace("{" + key + "}", value)
    return out


def render_generic(text):
    if md_lib:
        return md_lib.markdown(text, extensions=["tables", "attr_list"])
    return "<pre>" + html.escape(text) + "</pre>"


def render_weekly(doc):
    """Run the real builder, then swap its inlined <style> for a stylesheet link."""
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
        out = pathlib.Path(tmp.name)
    subprocess.run([sys.executable, "-I", str(WEEKLY_BUILDER), str(doc), str(CSS),
                    str(out), "--site"],
                   check=True, cwd=ROOT, capture_output=True)
    fragment = out.read_text(encoding="utf-8")
    out.unlink(missing_ok=True)
    # Everything from <div class="wrap"> onward is the body; the head matter
    # (title, font links, inlined style) is replaced by the shell.
    marker = '<div class="wrap">'
    body = fragment[fragment.index(marker) + len(marker):]
    body = re.sub(r"</div>\s*$", "", body.rstrip())
    title_m = re.search(r"<title>(.*?)</title>", fragment, re.S)
    return body, (title_m.group(1).strip() if title_m else doc.stem)


def issue_label(doc):
    m = re.search(r"^#\s+.*?Issue (\d+)", doc.read_text(encoding="utf-8"), re.M)
    return f"Issue {int(m.group(1)):02d}" if m else doc.stem


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "assets").mkdir(exist_ok=True)
    for css in (ROOT / "assets").glob("*.css"):
        (OUT / "assets" / css.name).write_text(css.read_text(encoding="utf-8"), encoding="utf-8")

    index = ['<header class="mast"><div class="over"><span>AI Safety Assessments</span></div>'
             "<h1>AI Safety Assessments</h1>"
             f'<p class="sub">{DESCRIPTION} Claim-level credibility ratings, origin mapping, '
             "falsifiable judgments with deadlines, and a public track record scored on "
             "resolution.</p></header>"]

    for section in SECTIONS:
        src = ROOT / section
        docs = sorted((d for d in src.glob("*.md")), reverse=True) if src.is_dir() else []
        if not docs:
            continue
        index.append(f"<h2>{html.escape(section.title())}</h2><ul>")
        for doc in docs:
            weekly = section == "reports" and doc.stem.endswith("-weekly")
            if weekly:
                try:
                    body, title = render_weekly(doc)
                except subprocess.CalledProcessError as exc:
                    # Issue 01 predates the v1.4+ structure the builder expects.
                    # One unrenderable issue must not fail the whole site build,
                    # so fall back to generic rendering and say so.
                    print(f"  WARNING: {doc.name} did not render through the weekly "
                          f"builder ({exc.returncode}); using generic rendering",
                          file=sys.stderr)
                    body = render_generic(doc.read_text(encoding="utf-8"))
                    title = doc.stem
                label = f"{issue_label(doc)} — {doc.stem[:10]}"
            else:
                body, title = render_generic(doc.read_text(encoding="utf-8")), doc.stem
                label = doc.stem
            target = OUT / section / (doc.stem + ".html")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                page(title, body, "../", f"{SITE}{section}/{doc.stem}.html"),
                encoding="utf-8")
            index.append(f'<li><a href="{section}/{doc.stem}.html">{html.escape(label)}</a></li>')
        index.append("</ul>")

    # About page, built from about.md at the repository root.
    about_src = ROOT / "about.md"
    if about_src.is_file():
        (OUT / "about").mkdir(exist_ok=True)
        (OUT / "about" / "index.html").write_text(
            page("How to read this", render_generic(about_src.read_text(encoding="utf-8")),
                 "../", f"{SITE}about/",
                 "The ratings, probability bands and corroboration statuses used in "
                 "AI Safety Assessments, and what an issue does and does not claim."),
            encoding="utf-8")
        index.append('<h2>About</h2><ul><li><a href="about/">How to read this</a>'
                     " — the ratings, the probability bands, and what an issue does "
                     "and does not claim</li></ul>")

    index.append(f'<div class="foot"><span>AI Safety Assessments</span>'
                 f'<span><a href="about/">How to read this</a></span>'
                 f'<span>Built {datetime.date.today().isoformat()}</span></div>')
    (OUT / "index.html").write_text(page("Index", "\n".join(index), "", SITE), encoding="utf-8")
    print(f"built {len(list(OUT.rglob('*.html')))} pages into {OUT}")


if __name__ == "__main__":
    main()
