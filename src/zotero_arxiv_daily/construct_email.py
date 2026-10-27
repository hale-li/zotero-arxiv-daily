from .protocol import Paper
import math
import re

CODE_URL_PATTERN = re.compile(
    r"https?://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", re.IGNORECASE
)
GITHUB_NON_REPO_OWNERS = {
    "features", "topics", "about", "pricing", "login", "apps", "marketplace",
    "orgs", "users", "sponsors", "collections", "trending", "explore",
    "settings", "notifications", "new", "security", "site",
}


def extract_code_url(paper: Paper) -> str | None:
    """Return the first GitHub repository URL mentioned in the paper text."""
    text = " ".join(part for part in (paper.full_text, paper.abstract) if part)
    if not text:
        return None
    for match in CODE_URL_PATTERN.finditer(text):
        owner, repo = match.group(1), match.group(2)
        if owner.lower() in GITHUB_NON_REPO_OWNERS:
            continue
        repo = re.sub(r"\.git$", "", repo).rstrip(".-_")
        if not repo:
            continue
        return f"https://github.com/{owner}/{repo}"
    return None


def _link_button(href: str, label: str, color: str = "#d9534f") -> str:
    return (
        f'<a href="{href}" style="display: inline-block; text-decoration: none; '
        f'font-size: 14px; font-weight: bold; color: #fff; background-color: {color}; '
        f'padding: 8px 16px; border-radius: 4px; margin: 0 8px 8px 0;">{label}</a>'
    )


framework = """
<!DOCTYPE HTML>
<html>
<head>
  <style>
    .star-wrapper {
      font-size: 1.3em; /* 调整星星大小 */
      line-height: 1; /* 确保垂直对齐 */
      display: inline-flex;
      align-items: center; /* 保持对齐 */
    }
    .half-star {
      display: inline-block;
      width: 0.5em; /* 半颗星的宽度 */
      overflow: hidden;
      white-space: nowrap;
      vertical-align: middle;
    }
    .full-star {
      vertical-align: middle;
    }
  </style>
</head>
<body>

<div>
    __CONTENT__
</div>

<br><br>
<div>
To unsubscribe, remove your email in your Github Action setting.
</div>

</body>
</html>
"""

def get_empty_html():
  block_template = """
  <table border="0" cellpadding="0" cellspacing="0" width="100%" style="font-family: Arial, sans-serif; border: 1px solid #ddd; border-radius: 8px; padding: 16px; background-color: #f9f9f9;">
  <tr>
    <td style="font-size: 20px; font-weight: bold; color: #333;">
        No Papers Today. Take a Rest!
    </td>
  </tr>
  </table>
  """
  return block_template

def get_block_html(title:str, authors:str, rate:str, tldr:str, pdf_url:str, affiliations:str=None, url:str=None, doi:str=None, code_url:str=None):
    buttons = []
    if pdf_url:
        buttons.append(_link_button(pdf_url, "PDF"))
    if url:
        buttons.append(_link_button(url, "Abstract", "#337ab7"))
    if code_url:
        buttons.append(_link_button(code_url, "Code", "#2f8f46"))
    buttons_html = "".join(buttons)
    if doi:
        doi_html = (
            '<tr><td style="font-size: 12px; color: #888; padding: 4px 0;">'
            f'DOI: <a href="https://doi.org/{doi}" style="color: #888;">{doi}</a>'
            '</td></tr>'
        )
    else:
        doi_html = ""

    block_template = """
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="font-family: Arial, sans-serif; border: 1px solid #ddd; border-radius: 8px; padding: 16px; background-color: #f9f9f9;">
    <tr>
        <td style="font-size: 20px; font-weight: bold; color: #333;">
            {title}
        </td>
    </tr>
    <tr>
        <td style="font-size: 14px; color: #666; padding: 8px 0;">
            {authors}
            <br>
            <i>{affiliations}</i>
        </td>
    </tr>
    <tr>
        <td style="font-size: 14px; color: #333; padding: 8px 0;">
            <strong>Relevance:</strong> {rate}
        </td>
    </tr>
    <tr>
        <td style="font-size: 14px; color: #333; padding: 8px 0;">
            <strong>TLDR:</strong> {tldr}
        </td>
    </tr>

    <tr>
        <td style="padding: 8px 0;">
            {buttons}
        </td>
    </tr>
    {doi_line}
</table>
"""
    return block_template.format(title=title, authors=authors,rate=rate, tldr=tldr, pdf_url=pdf_url, affiliations=affiliations, buttons=buttons_html, doi_line=doi_html)

def get_stars(score:float):
    full_star = '<span class="full-star">⭐</span>'
    half_star = '<span class="half-star">⭐</span>'
    low = 6
    high = 8
    if score <= low:
        return ''
    elif score >= high:
        return full_star * 5
    else:
        interval = (high-low) / 10
        star_num = math.ceil((score-low) / interval)
        full_star_num = int(star_num/2)
        half_star_num = star_num - full_star_num * 2
        return '<div class="star-wrapper">'+full_star * full_star_num + half_star * half_star_num + '</div>'


def render_email(papers:list[Paper]) -> str:
    parts = []
    if len(papers) == 0 :
        return framework.replace('__CONTENT__', get_empty_html())
    
    for p in papers:
        #rate = get_stars(p.score)
        rate = round(p.score, 1) if p.score is not None else 'Unknown'
        author_list = [a for a in p.authors]
        num_authors = len(author_list)
        if num_authors <= 5:
            authors = ', '.join(author_list)
        else:
            authors = ', '.join(author_list[:3] + ['...'] + author_list[-2:])
        if p.affiliations is not None:
            affiliations = p.affiliations[:5]
            affiliations = ', '.join(affiliations)
            if len(p.affiliations) > 5:
                affiliations += ', ...'
        else:
            affiliations = 'Unknown Affiliation'
        parts.append(get_block_html(p.title, authors, rate, p.tldr, p.pdf_url, affiliations, p.url, p.doi, extract_code_url(p)))

    content = '<br>' + '</br><br>'.join(parts) + '</br>'
    return framework.replace('__CONTENT__', content)
