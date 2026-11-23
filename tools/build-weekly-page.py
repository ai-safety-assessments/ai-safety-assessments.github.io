#!/usr/bin/env python3
"""Render a weekly issue's markdown into the existing weekly page design.
Structure-aware, no substantive edits: only markup conversion.

Masthead values are read from the draft's front matter (added 2026-09-21, after the
Issue 03 run had to patch a hard-coded Issue 02 masthead by hand):
  - issue number: the `# ... Issue N` title line
  - period, late-item range and published date: the `**Period covered:** ... · **Published:** ...` line
  - headline: an optional `**Headline:**` front-matter line; if absent, the first sentence of the
    §1 BLUF paragraph after "Bottom line."
  - methodology version for the footer: `**Version:** x.y` in claude/methodology.md next to tools/
  - next issue: published date + 7 days
Evidence references (added 2026-11-02, Darryl): the markdown keeps the `[E-n]` form, which the lint,
the register and the verification tools read; the page renders each as a bare number, `[4]`, linked to
the evidence-table row, which carries `id="e4"`. Lists such as `[E-4, E-5]` render as `[4, 5]` with each
number linked; the table's # and Corr. columns show bare linked numbers too. Prior-issue identifiers
(`Issue-1 E-12`) are left as written.
Usage: python3 tools/build-weekly-page.py reports/YYYY-MM-DD-weekly.md <live-html> <out.html>
"""
import re, sys, html, os, datetime

SRC = sys.argv[1]
LIVE = sys.argv[2]   # live artifact html, OR a .css file (added 2026-11-14)
OUT = sys.argv[3]

md = open(SRC, encoding='utf-8').read()
# Two ways to get the stylesheet. Historically the CSS was sliced back out of
# the live artifact page, which made the published page the source of truth for
# styling and let the injected rules below accumulate one copy per build.
# Passing a .css file instead makes the repository the source of truth; the
# live-html path is kept so preflight.py and older callers still work.
USING_STYLESHEET = LIVE.lower().endswith('.css')
# --site: the published-website build. The standing definitions move to the
# About page instead of repeating in every issue (Darryl, 2026-11-14).
SITE_MODE = '--site' in sys.argv[4:]
ABOUT_HREF = '../about/'
live = '' if USING_STYLESHEET else open(LIVE, encoding='utf-8').read()

# ---------- masthead values from the front matter ----------
_front = md.split('\n## ', 1)[0]
_m = re.search(r'^# .*?Issue (\d+)', _front, re.M)
ISSUE_NO = int(_m.group(1)) if _m else 0
ISSUE_LABEL = f'Issue {ISSUE_NO:02d}'
_m = re.search(r'\*\*Period covered:\*\*\s*(.+?)(?:\s*\(|\s*·)', _front)
PERIOD = _m.group(1).strip() if _m else ''
_m = re.search(r'late items from ([^)]+?) marked', _front)
LATE_RANGE = _m.group(1).strip() if _m else ''
_m = re.search(r'\*\*Published:\*\*\s*(\d{1,2} [A-Z][a-z]{2} \d{4})', _front)
PUBLISHED = _m.group(1) if _m else ''
try:
    _d = datetime.datetime.strptime(PUBLISHED, '%d %b %Y')
    NEXT_ISSUE = (_d + datetime.timedelta(days=7)).strftime('Mon %-d %b %Y')
except ValueError:
    NEXT_ISSUE = ''
_m = re.search(r'^\*\*Headline:\*\*\s*(.+)$', _front, re.M)
HEADLINE = _m.group(1).strip() if _m else ''
if not HEADLINE:
    _b = re.search(r'\*\*Bottom line\.\*\*\s*(.+?[.!?])(?:\s|$)', md)
    HEADLINE = _b.group(1).strip() if _b else ''
METH_VERSION = ''
try:
    _mt = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'claude', 'methodology.md'), encoding='utf-8').read()
    _m = re.search(r'\*\*Version:\*\*\s*([\d.]+)', _mt)
    METH_VERSION = _m.group(1) if _m else ''
except OSError:
    pass

# ---------- CSS from the live page (between first <style> after <link ...> and </style>) ----------
if USING_STYLESHEET:
    css = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
           '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
           '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
           'family=Archivo:wght@500;600;700&family=Source+Serif+4:ital,opsz,wght@'
           '0,8..60,400;0,8..60,600;1,8..60,400&family=IBM+Plex+Mono:wght@400;500;600'
           '&display=swap">\n<style>\n'
           + open(LIVE, encoding='utf-8').read() + '\n</style>')
else:
    css_start = live.index('<link rel="stylesheet"')
    css_end = live.index('</style>', css_start) + len('</style>')
    css = live[css_start:css_end]
# Live-html path only: the stylesheet file already carries these rules, and
# re-injecting them is what produced eleven copies of code{} in the live page.
if not USING_STYLESHEET and '.bluf{' not in css:
    css = css.replace('@media (prefers-reduced-motion:no-preference)',
                      '.bluf{font-size:17px; line-height:1.6; margin:18px 0 22px; max-width:70ch;}\n@media (prefers-reduced-motion:no-preference)')
# evidence-reference links (2026-11-02): highlight the target row and keep it clear of the top edge
if 'tr:target' not in css:
    css = css.replace('@media (prefers-reduced-motion:no-preference)',
                      'a.ref{text-decoration:none; font-variant-numeric:tabular-nums;}\na.ref:hover{text-decoration:underline;}\ntr[id]{scroll-margin-top:24px;}\ntr:target td{background:var(--kj-bg);}\n@media (prefers-reduced-motion:no-preference)')
if not USING_STYLESHEET:
    css = css.replace('@media (prefers-reduced-motion:no-preference)',
                  'code{font-family:"IBM Plex Mono",monospace; font-size:.86em; color:var(--code); background:var(--na-bg); padding:0 4px; border-radius:3px;}\n@media (prefers-reduced-motion:no-preference)')

# ---------- inline conversion ----------
# Hover/focus definitions, worded exactly as the Key Judgments front matter has
# always worded them, so the page says nothing new.
YARDSTICK = {
    'remote chance': '>0-~5%', 'highly unlikely': '~10-20%', 'unlikely': '~25-35%',
    'realistic possibility': '~40-<50%', 'likely': '~55-75%', 'probable': '~55-75%',
    'highly likely': '~80-90%', 'almost certain': '~95-<100%',
}
STATUS = {
    'established': 'Confirmed across independent origins.',
    'single-origin credible': 'From one solid source, not independently confirmed.',
    'contested': 'Credible evidence points both ways.',
    'unsubstantiated': 'Asserted, not yet supported.',
}
SOURCE_AXIS = {
    'A': 'strong track record, or a primary source speaking against its own interest',
    'B': 'primary source, neutral incentive, methodology visible',
    'C': 'primary but self-flattering, or reputable secondary with named sourcing',
    'D': 'weakly sourced, or interested party without methodology',
    'E': 'known-unreliable channel', 'F': 'cannot be judged',
}
INFO_AXIS = {
    '1': 'confirmed by independent origins',
    '2': 'consistent with other reporting, not independently confirmed',
    '3': 'plausible, uncorroborated', '4': 'doubtful',
    '5': 'contradicted by other evidence', '6': 'cannot be judged',
}
SUB_SITE = ('<p class="sub">Evidence-graded assessment of AI safety developments. '
            'Hover or tap any rating, band or status for its meaning; '
            '<a href="' + ABOUT_HREF + '">How to read this</a> has the full scheme.</p>')


CONFIDENCE = {
    'high': 'Two or more independent origins, no credible contradiction, and at least '
            'one against-interest or track-recorded source.',
    'moderate': 'No credible contradiction, but key evidence is single-origin or one '
                'load-bearing assumption is unsupported.',
    'low': 'Single-origin and self-interested, or an untestable load-bearing '
           'assumption, or credible contradicting evidence exists.',
}
CONFIDENCE_NOTE = (' Confidence describes how fragile the band is under further '
                   'evidence, not how probable the claim is.')
AUDIENCE = {
    'decision-makers': 'Funders, organisation leads and policymakers.',
    'contributors': 'People choosing where to work or contribute in the field.',
    'public': 'General readers, with no professional stake assumed.',
}
AXIS = {
    'capability pace': 'How fast frontier capability is advancing.',
    'misalignment incidence': 'How often misaligned behaviour is observed.',
    'governance response': 'How far and how fast binding governance moves.',
    'developer conduct': 'What frontier model developers choose to do.',
    'geopolitics and diffusion': 'How capability spreads across states and actors.',
    'other': 'No standing axis fits this judgment.',
}
AXIS_NOTE = (' The axis groups judgments by the strategic question their resolution '
             'informs; it is fixed when the judgment is registered.')
ORIGIN_TIP = ('Origin identifier. Items sharing an origin trace back to the same '
              'underlying record and are counted once, however many outlets carried '
              'it.')
EVIDENCE = {}   # row number -> short description, filled once section 5 is parsed


def tip_attr(text):
    # data-tip drives the styled bubble; title is the fallback inside the
    # evidence table, whose scroll box would clip an absolutely positioned one.
    esc = html.escape(text, quote=True)
    return ' class="tip" tabindex="0" data-tip="%s" title="%s"' % (esc, esc)

RT_CLASS = {'A':'rt-a','B':'rt-b','C':'rt-c','D':'rt-d','E':'rt-d','F':'rt-f'}
def chip(code):
    letter, digit = code[0], code[1]
    tip = 'Source %s: %s. Information %s: %s.' % (
        letter, SOURCE_AXIS.get(letter, '?'), digit, INFO_AXIS.get(digit, '?'))
    # One class attribute: tip_attr() carries its own class="tip", and a second
    # class attribute on the same element is ignored by browsers, which had left
    # rating chips without the tooltip styling (found 2026-11-23).
    esc = html.escape(tip, quote=True)
    return (f'<span class="rt {RT_CLASS[letter]} tip" tabindex="0" '
            f'data-tip="{esc}" title="{esc}">{code}</span>')

def chips(s):
    """'A2 / C3' or 'B2/C3' -> chips joined by ' / '"""
    parts = [p.strip() for p in s.split('/')]
    return ' / '.join(chip(p) for p in parts)

def ref_link(n):
    row = EVIDENCE.get(str(n))
    if row:
        return f'<a class="ref tip" href="#e{n}" data-tip="{html.escape(row, quote=True)}"' \
               f' title="{html.escape(row, quote=True)}">{n}</a>'
    return f'<a class="ref" href="#e{n}">{n}</a>'

def refs(s):
    """'[E-4, E-5]' -> '[4, 5]' with each number linked to its evidence-table row"""
    s = re.sub(r'\[(E-\d+(?:,\s*E-\d+)*)\]',
               lambda m: '[' + ', '.join(ref_link(x.strip()[2:]) for x in m.group(1).split(',')) + ']', s)
    # a bare 'E-n' (in table notes, say) becomes 'row n', linked; 'Issue-8 E-4' (a prior issue's row) is left alone
    s = re.sub(r'(Issue-\d+ )?(?<![\w-])E-(\d+)\b',
               lambda m: m.group(0) if m.group(1) else 'row ' + ref_link(m.group(2)), s)
    return s.replace('[E-n]', '[n]')

TERM_RE = re.compile(
    r'\*\*(' + '|'.join(sorted(list(YARDSTICK) + list(STATUS),
                                key=len, reverse=True)) + r')\*\*', re.I)


def term_tip(m):
    """A bolded yardstick band or finding status keeps its bold and gains a definition."""
    word = m.group(1)
    key = word.lower()
    text = ('PHIA Probability Yardstick: %s' % YARDSTICK[key]) if key in YARDSTICK else STATUS[key]
    return f'<strong{tip_attr(text)}>{word}</strong>'


STATUS_RE = re.compile(
    r'\*\*Finding &mdash; |\*\*Finding — (' +
    '|'.join(sorted(STATUS, key=len, reverse=True)) + r')\b', re.I)


def status_tip(m):
    """The §1 blocks bold the whole 'Finding — <status>' label, so the status is
    tagged inside the bold rather than by TERM_RE."""
    word = m.group(1)
    if not word:
        return m.group(0)
    return f'**Finding — <span{tip_attr(STATUS[word.lower()])}>{word}</span>'


CONF_RE = re.compile(r'\b(High|Moderate|Low) confidence\b')
AXIS_RE = re.compile(r'\*\*(' + '|'.join(sorted(AXIS, key=len, reverse=True)) + r')\*\*', re.I)


def conf_tip(m):
    word = m.group(1)
    return f'<span{tip_attr(CONFIDENCE[word.lower()] + CONFIDENCE_NOTE)}>{word} confidence</span>'


def axis_tip(m):
    word = m.group(1)
    return f'<strong{tip_attr(AXIS[word.lower()] + AXIS_NOTE)}>{word}</strong>'


def inline(s):
    s = html.escape(s, quote=False)
    s = CONF_RE.sub(conf_tip, s)
    s = AXIS_RE.sub(axis_tip, s)
    s = STATUS_RE.sub(status_tip, s)
    s = TERM_RE.sub(term_tip, s)
    # links [text](url)
    s = re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)', r'<a href="\2">\1</a>', s)
    # evidence references [E-n] -> [n], linked to the table row
    s = refs(s)
    # rating tokens **B2**, **A2 / C3**, **B2/C3**
    s = re.sub(r'\*\*([A-F][1-6](?:\s*/\s*[A-F][1-6])?)\*\*', lambda m: chips(m.group(1)), s)
    # bold / italic / code
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<![\w*])\*([^*]+?)\*(?![\w*])', r'<em>\1</em>', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    return s

def area_lead(text):
    """'**[Area · Area2] Title.** rest' -> '<span class="area">..</span> <strong>Title.</strong> rest'
       '**[Area]** rest' -> '<span class="area">..</span> rest'"""
    m = re.match(r'\*\*\[([^\]]+)\]\s*(.*?)\*\*\s*(.*)$', text, re.S)
    if not m:
        return inline(text)
    area, title, rest = m.groups()
    out = f'<span class="area">{html.escape(area, quote=False)}</span>'
    if title.strip():
        out += f' <strong>{inline(title.strip())}</strong>'
    if rest.strip():
        out += ' ' + inline(rest.strip())
    return out

# ---------- split into sections ----------
lines = md.split('\n')
sections = {}
cur = None
for ln in lines:
    m = re.match(r'^##\s+(\d)\.\s+(.*)$', ln)
    if m:
        cur = m.group(1); sections[cur] = []; continue
    if cur:
        sections[cur].append(ln)

# Evidence-row previews for the [n] references in the body. Parsed here, before
# the body is emitted, because the refs appear in sections 1-4 while the table
# itself is section 5.
for _r in [l for l in sections.get('5', []) if l.startswith('| E-')]:
    _c = [c.strip() for c in _r.strip().strip('|').split('|')]
    if len(_c) == 8:
        _num = _c[0][2:] if _c[0].startswith('E-') else _c[0]
        _src = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', _c[1])   # drop markdown links
        _src = re.sub(r'[*`]', '', _src).strip()
        _rating = re.sub(r'[*`]', '', _c[4]).strip()
        EVIDENCE[_num] = f'{_src} - rated {_rating}'


def paras(block):
    """group lines into blocks separated by blank lines; keep list items as separate items"""
    out, buf = [], []
    for ln in block:
        if ln.strip() == '' or ln.strip() == '---':
            if buf: out.append(buf); buf = []
        else:
            buf.append(ln)
    if buf: out.append(buf)
    return out

body = []
A = body.append
# Section boundaries, so the site build can reorder and collapse sections
# after emission without touching how each section is rendered.
_SEC = []
def _mark(key):
    _SEC.append((key, len(body)))

# ---------- Section 1 ----------
s1 = sections['1']
blocks = paras(s1)
# intro: first block (4 lines) -> notes
intro = blocks[0]
_mark('1')
A('<h2 id="kj"><span class="n">Section 1</span>Key judgments</h2>')
if SITE_MODE:
    # Definitions, identical every issue: on the site they live on the About
    # page and on the terms themselves, so section 1 opens with the BLUF.
    pass
else:
    A('<p class="note">' + inline(intro[0]) + ' ' + inline(intro[1]) + '</p>'
      '<p class="note">' + inline(intro[2]) + '</p>'
      '<p class="note">' + inline(intro[3]) + '</p>')
for blk in blocks[1:]:
    head = blk[0]
    m = re.match(r'\*\*(KJ-\d+) — (.*?)\.?\*\*\s*\*Audience:\s*(.*?)\.?\*\s*$', head)
    if not m:
        # BLUF paragraph (methodology §4.1): any non-KJ block between the notes and KJ-1
        A('<p class="bluf">' + inline(' '.join(blk)) + '</p>')
        continue
    kj, title, aud = m.groups()
    # v1.8: the italic span may carry "Axis: <term>" after the audience; render it as its own chip
    axis = None
    xm = re.match(r'(.*?)\.?\s*Axis:\s*(.+?)\.?$', aud)
    if xm:
        aud, axis = xm.group(1).strip(), xm.group(2).strip()
    def _aud_span(name):
        key = name.strip().lower()
        if key in AUDIENCE:
            return f'<span{tip_attr(AUDIENCE[key])}>{html.escape(name.strip())}</span>'
        return html.escape(name.strip())

    aud_html = ', '.join(_aud_span(a) for a in aud.split(','))
    tag = f'{kj} · {inline(title)} · for: {aud_html}'
    if axis:
        _k = axis.lower().rstrip('.')
        _inner = (f'<span{tip_attr(AXIS[_k] + AXIS_NOTE)}>{html.escape(axis)}</span>'
                  if _k in AXIS else html.escape(axis))
        tag += f' · axis: {_inner}'
    A(f'<div class="kj"><span class="tag">{tag}</span>')
    for ln in blk[1:]:
        ln = re.sub(r'^Finding — \*\*(.+?)\*\*', r'**Finding — \1**', ln)
        ln = re.sub(r'^Judgment — ', r'**Judgment** — ', ln)
        ln = re.sub(r'^Implication — ', r'**Implication** — ', ln)
        A('<p>' + inline(ln) + '</p>')
    A('</div>')

# ---------- Section 2 ----------
s2 = paras(sections['2'])
_mark('2')
A('<h2 id="chg"><span class="n">Section 2</span>Changes from prior assessment</h2>')
# optional intro paragraph(s) before the list; the rule itself lives in the front matter
i = 0
while i < len(s2) and not s2[i][0].startswith('- '):
    A('<p>' + inline(' '.join(s2[i])) + '</p>'); i += 1
A('<ul>')
for ln in s2[i]:
    ln = ln[2:] if ln.startswith('- ') else ln
    ln = ln.replace('( ', '(')  # stray spaces after opening parenthesis in labels
    A('<li>' + inline(ln) + '</li>')
A('</ul>')
for b in s2[i+1:]:
    txt = ' '.join(b)
    cls = ' class="note"' if txt.startswith('Resolved signposts') else ''
    A(f'<p{cls}>' + inline(txt) + '</p>')

# ---------- Section 3 ----------
s3 = sections['3']
# split into subsections
subs, cur = [], None
pre = []
for ln in s3:
    m = re.match(r'^###\s+(3\.\d)\s+(.*)$', ln)
    if m:
        cur = [m.group(1), m.group(2), []]; subs.append(cur); continue
    (cur[2] if cur else pre).append(ln)
sec3_note = [l for l in pre if l.strip()][0]
ids = {'3.1':'inc','3.2':'tech','3.3':'soc','3.4':'pol','3.5':'developers'}
first = True
for num, title, blk in subs:
    _mark(num)
    A(f'<h2 id="{ids[num]}"><span class="n">Section {num}</span>{html.escape(title, quote=False)}</h2>')
    if first:
        # Reading mechanics, identical every issue: About page on the site.
        if not SITE_MODE:
            A('<p class="note">' + inline(sec3_note) + '</p>')
        first = False
    in_ul = False
    for b in paras(blk):
        for ln in b:
            if ln.startswith('- '):
                if not in_ul: A('<ul>'); in_ul = True
                A('<li>' + area_lead(ln[2:]) + '</li>')
            else:
                if in_ul: A('</ul>'); in_ul = False
                m = re.match(r'^\*\*([^\[][^*]+?)\.\*\*\s+(.*)$', ln)
                if m and not ln.startswith('**['):
                    A(f'<h3>{inline(m.group(1))}</h3>')
                    A('<p>' + inline(m.group(2)) + '</p>')
                elif ln.startswith('**['):
                    A('<p>' + area_lead(ln) + '</p>')
                else:
                    A('<p>' + inline(ln) + '</p>')
    if in_ul: A('</ul>')

# ---------- Section 4 ----------
_mark('4')
A('<h2 id="watch"><span class="n">Section 4</span>Watchlist — signposts for coming weeks</h2>')
for l in [l for l in sections['4'] if l.strip() and not l.startswith('- ')]:
    A('<p class="note">' + inline(l) + '</p>')
A('<ul class="watch">')
for ln in [l for l in sections['4'] if l.startswith('- ')]:
    A('<li>' + inline(ln[2:]) + '</li>')
A('</ul>')

# ---------- Section 5 ----------
s5 = sections['5']
note = [l for l in s5 if l.strip() and not l.startswith('|')][0]
_mark('5')
A('<h2 id="ev"><span class="n">Section 5</span>Evidence table</h2>')
_note_html = inline(note)
if SITE_MODE:
    # The ratings are no longer defined in section 1 on the site.
    _note_html = _note_html.replace(
        'defined in Section 1', f'defined in <a href="{ABOUT_HREF}">How to read this</a>')
A('<p class="note">' + _note_html + '</p>')
rows = [l for l in s5 if l.startswith('| E-')]
A('<div class="tablewrap"><table>')
A('<thead><tr><th>#</th><th>Source</th><th>Origin</th><th>Claim actually made</th><th>Rating</th><th>Supports</th><th>Corr.</th><th>Notes</th></tr></thead>')
A('<tbody>')
for r in rows:
    cells = [c.strip() for c in r.strip().strip('|').split('|')]
    assert len(cells) == 8, (len(cells), r[:60])
    num, src, org, claim, rating, sup, corr, notes = cells
    n = num[2:] if num.startswith('E-') else num
    corr_html = ', '.join(ref_link(c.strip()[2:]) if re.fullmatch(r'E-\d+', c.strip()) else inline(c.strip())
                          for c in corr.split(',')) if re.search(r'E-\d', corr) else inline(corr)
    # data-l carries the column name so the stylesheet can stack each row into
    # a labelled block below 700px, where eight columns cannot fit on a phone.
    A(f'<tr id="e{n}">'
      f'<td class="num" data-l="#">{n}</td>'
      f'<td data-l="Source">{inline(src)}</td>'
      f'<td class="mono tip" data-l="Origin" data-tip="{html.escape(ORIGIN_TIP, quote=True)}"'
      f' title="{html.escape(ORIGIN_TIP, quote=True)}">{org}</td>'
      f'<td data-l="Claim actually made">{inline(claim)}</td>'
      f'<td data-l="Rating">{chips(rating)}</td>'
      f'<td class="mono" data-l="Supports">{inline(sup)}</td>'
      f'<td class="mono" data-l="Corroborated by">{corr_html}</td>'
      f'<td data-l="Notes">{inline(notes)}</td>'
      '</tr>')
A('</tbody>')
A('</table></div>')

# ---------- Section 6 ----------
_mark('6')
if SITE_MODE:
    # On the site the source summary sits directly under the key judgments it
    # qualifies, unnumbered, so sections 2-5 keep the numbers every in-text
    # cross-reference in every issue already uses.
    A('<h2 id="srcsum"><span class="n">The evidence behind these judgments</span>Source summary</h2>')
else:
    A('<h2 id="srcsum"><span class="n">Section 6</span>Source summary statement</h2>')
A('<div class="src">')
for b in paras(sections['6']):
    A('<p>' + inline(' '.join(b)) + '</p>')
A('</div>')

_mark('foot')
_meth = (f'<a href="{ABOUT_HREF}">How to read this</a>' if SITE_MODE
         else 'Adapted Admiralty (categorical) + PHIA yardstick')
A(f'<div class="foot"><span>AI Safety Assessments · {ISSUE_LABEL}</span>'
  f'<span>{_meth}' + (f' · method v{METH_VERSION}' if METH_VERSION else '') + '</span>'
  f'<span>Next issue: {NEXT_ISSUE}</span></div>')

# ---------- head / masthead (from live) ----------
# optional front-matter coverage line: '**Coverage:** ...' before the first '## ' heading
front = md.split('\n## ', 1)[0]
cov_line = next((l for l in front.split('\n') if l.startswith('**Coverage:**')), None)
if cov_line:
    t = cov_line[len('**Coverage:**'):].strip()
    if SITE_MODE:
        # The taxonomy list is reference material (About page). What stays is
        # the caveat about this issue: omission is not evidence of quiet.
        _om = re.search(r'Only areas\b.*$', t)
        if _om:
            t = _om.group(0)
    cov_html = '\n  <p class="sub" style="margin-top:10px"><strong>Coverage.</strong> ' + inline(t[0].upper() + t[1:]) + '</p>'
else:
    cov_html = ''
# dated addition / correction notes in the front matter: '**Added <date>:** …', '**Corrected <date>:** …'
for l in front.split('\n'):
    m = re.match(r'\*\*((?:Added|Corrected)[^*]*?):?\*\*\s*(.*)$', l)
    if m:
        cov_html += '\n  <p class="sub" style="margin-top:10px"><strong>' + html.escape(m.group(1)) + '.</strong> ' + inline(m.group(2)[0].upper() + m.group(2)[1:]) + '</p>'
head = '''<title>AI Safety Assessments</title>
''' + css + '''

<div class="wrap">
<header class="mast">
  <div class="over"><span>AI Safety Assessments</span><span>''' + ISSUE_LABEL + '''</span><span>Period ''' + html.escape(PERIOD, quote=False) + '''</span><span>Published ''' + html.escape(PUBLISHED, quote=False) + '''</span></div>
  <h1>''' + html.escape(HEADLINE, quote=False) + '''</h1>
  <p class="sub">Evidence-graded weekly assessment across technical AI safety, security, societal impacts, and governance. Findings carry a corroboration status; estimative judgments use the PHIA Probability Yardstick, name their audience and the axis of uncertainty they bear on, and close with the decision their resolution would inform. <span class="rt rt-b">B2</span>-style chips are adapted Admiralty ratings, categorical only, never scored. Each development links its primary source; a bracketed number such as [4] links to that row of the evidence table. Row, origin and judgment identifiers restart each issue; a prior issue's are written <code>Issue-1 KJ-n</code>. Section 2 lists only prior judgments with a significant development this week (a resolution, a re-rating, or new evidence bearing on how the judgment is likely to resolve); every judgment, open or resolved, is tracked in the calibration register. ''' + ('Late items from ' + html.escape(LATE_RANGE, quote=False) + ' are marked, as are newly disclosed incidents whose events predate the window.' if LATE_RANGE else '') + '''</p>''' + cov_html + '''
</header>
<nav class="toc" aria-label="Sections">
  <a href="#kj">1 Key judgments</a><a href="#chg">2 Changes</a><a href="#inc">3.1 Evals, incidents &amp; security</a><a href="#tech">3.2 Technical safety</a><a href="#soc">3.3 Societal impacts</a><a href="#pol">3.4 Policy &amp; governance</a><a href="#developers">3.5 Frontier model developers &amp; industry</a><a href="#watch">4 Watchlist</a><a href="#ev">5 Evidence table</a><a href="#srcsum">6 Source summary</a>
</nav>
'''

if SITE_MODE:
    _m = re.search(r'<p class="sub">Evidence-graded weekly assessment.*?</p>', head, re.S)
    if _m:
        head = head.replace(_m.group(0), SUB_SITE)

    # Order: key judgments, the source summary that qualifies them, then the
    # numbered sections. Everything after the source summary starts collapsed.
    _bounds = _SEC + [('end', len(body))]
    _chunks = {k: body[a:b] for (k, a), (_k2, b) in zip(_bounds, _bounds[1:])}
    _sub_keys = [n for n, _t, _b in subs]
    _order = ['1', '6', '2'] + _sub_keys + ['4', '5']

    def _collapsed(chunk):
        h2, rest = chunk[0], chunk[1:]
        txt = ''.join(rest)
        # developments in section 3 are area-tagged paragraphs, not list items
        rows = txt.count('<tr id="e')
        items = txt.count('class="area"') or txt.count('<li')
        count = (f'{rows} rows' if rows else
                 f'{items} item' + ('' if items == 1 else 's') if items else '')
        if count:
            h2 = h2.replace('</h2>', f' <span class="sec-count">{count}</span></h2>', 1)
        return (['<details class="sec">', f'<summary>{h2}</summary>', '<div class="sec-body">']
                + rest + ['</div>', '</details>'])

    _new = body[:_bounds[0][1]]
    for _k in _order:
        _c = _chunks.get(_k)
        if _c:
            _new += _c if _k in ('1', '6') else _collapsed(_c)
    _new += _chunks.get('foot', [])
    body = _new

    _titles = {'3.1': 'Evals, incidents &amp; security', '3.2': 'Technical safety',
               '3.3': 'Societal impacts', '3.4': 'Policy &amp; governance',
               '3.5': 'Frontier model developers &amp; industry'}
    _nav = ('<nav class="toc" aria-label="Sections">\n'
            '  <a href="#kj">1 Key judgments</a><a href="#srcsum">Source summary</a>'
            '<a href="#chg">2 Changes</a>'
            + ''.join(f'<a href="#{ids[k]}">{k} {_titles.get(k, k)}</a>' for k in _sub_keys)
            + '<a href="#watch">4 Watchlist</a><a href="#ev">5 Evidence table</a>'
            '<button class="toggle-all" type="button" aria-pressed="false">Expand all</button>\n'
            '</nav>')
    head = re.sub(r'<nav class="toc".*?</nav>', lambda _x: _nav, head, count=1, flags=re.S)

open(OUT, 'w', encoding='utf-8').write(head + '\n' + '\n'.join(body) + '\n</div>\n')
print('rows:', len(rows), 'bytes:', len(head) + sum(len(b) for b in body))
