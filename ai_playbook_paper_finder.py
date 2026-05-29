#!/usr/bin/env python3
"""
AI Playbook Paper Finder

Searches public scholarly metadata APIs for candidate peer-reviewed papers in
public administration, public policy, and closely related fields. The output is
intended as a starting point for Assignment 3: 7-Paper Pilot & Fidelity
Assessment.

Run:
    python ai_playbook_paper_finder.py

Outputs:
    paper_candidates.csv
    paper_finder_report.md
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import textwrap
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple


CROSSREF_API = "https://api.crossref.org/works"
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"

OUTPUT_CSV = "paper_candidates.csv"
OUTPUT_MD = "paper_finder_report.md"

DEFAULT_ROWS_PER_QUERY = 12
DEFAULT_TARGET_PER_CATEGORY = 7
DEFAULT_START_YEAR = 2000
DEFAULT_SLEEP_SECONDS = 1.0

# Add your email if you want Crossref to route requests through its polite pool.
# Example:
# CONTACT_EMAIL = "your.name@example.edu"
CONTACT_EMAIL = ""


PUBLIC_ADMIN_TERMS = [
    '"public administration"',
    '"public policy"',
    '"public management"',
    '"public sector"',
    '"governance"',
    '"government performance"',
    '"policy implementation"',
    '"administrative burden"',
    '"bureaucracy"',
    '"street-level bureaucracy"',
    '"nonprofit management"',
]


METHODOLOGY_SEARCH_TERMS: Dict[str, List[str]] = {
    "Quantitative": [
        "regression",
        "survey",
        "panel data",
        "administrative data",
        "statistical analysis",
        "structural equation",
    ],
    "Qualitative": [
        "interview",
        "case study",
        "ethnography",
        "focus group",
        "thematic analysis",
        "grounded theory",
    ],
    "Mixed Methods": [
        '"mixed methods"',
        '"mixed-methods"',
        "survey interviews",
        "qualitative quantitative",
        "sequential explanatory",
        "convergent design",
    ],
    "Theoretical": [
        "theory",
        "conceptual framework",
        "model",
        "typology",
        "normative theory",
        "theoretical framework",
    ],
    "Experimental": [
        "experiment",
        "field experiment",
        "randomized",
        "RCT",
        "vignette experiment",
        "survey experiment",
    ],
    "Meta-Analysis": [
        '"meta-analysis"',
        '"meta analysis"',
        "effect size",
        "pooled estimate",
        "systematic quantitative review",
    ],
    "Systematic Review": [
        '"systematic review"',
        "scoping review",
        "PRISMA",
        "evidence synthesis",
        "literature review protocol",
    ],
}


METHODOLOGY_KEYWORDS: Dict[str, List[str]] = {
    "Quantitative": [
        "regression",
        "logit",
        "probit",
        "survey",
        "statistical",
        "quantitative",
        "panel data",
        "administrative data",
        "structural equation",
        "multilevel",
        "difference-in-differences",
        "instrumental variable",
        "propensity score",
    ],
    "Qualitative": [
        "interview",
        "case study",
        "case-study",
        "ethnography",
        "focus group",
        "thematic analysis",
        "grounded theory",
        "participant observation",
        "content analysis",
        "qualitative",
        "process tracing",
    ],
    "Mixed Methods": [
        "mixed methods",
        "mixed-methods",
        "mixed method",
        "qualitative and quantitative",
        "quantitative and qualitative",
        "sequential explanatory",
        "convergent design",
        "triangulation",
        "multi-method",
        "multimethod",
    ],
    "Theoretical": [
        "theory",
        "theoretical",
        "conceptual",
        "framework",
        "model",
        "typology",
        "normative",
        "proposition",
        "agenda",
    ],
    "Experimental": [
        "experiment",
        "experimental",
        "field experiment",
        "randomized",
        "randomised",
        "random assignment",
        "treatment",
        "control group",
        "rct",
        "vignette",
        "survey experiment",
    ],
    "Meta-Analysis": [
        "meta-analysis",
        "meta analysis",
        "effect size",
        "pooled",
        "heterogeneity",
        "forest plot",
        "publication bias",
    ],
    "Systematic Review": [
        "systematic review",
        "scoping review",
        "prisma",
        "evidence synthesis",
        "review protocol",
        "search strategy",
        "screening",
        "inclusion criteria",
    ],
}


PUBLIC_ADMIN_KEYWORDS = [
    "public administration",
    "public policy",
    "public management",
    "public sector",
    "governance",
    "government",
    "bureaucracy",
    "policy implementation",
    "administrative",
    "civil service",
    "nonprofit",
    "public service",
]


JOURNAL_HINTS = [
    "public administration review",
    "journal of public administration research and theory",
    "public administration",
    "governance",
    "public management review",
    "policy studies journal",
    "journal of policy analysis and management",
    "administration & society",
    "american review of public administration",
    "international public management journal",
]


@dataclass
class PaperCandidate:
    title: str
    authors: List[str] = field(default_factory=list)
    year: str = ""
    journal_or_venue: str = ""
    doi: str = ""
    url: str = ""
    abstract: str = ""
    suggested_methodology_category: str = ""
    one_sentence_justification: str = ""
    apa_style_citation_draft: str = ""
    source_api: str = ""
    search_category: str = ""
    publication_types: List[str] = field(default_factory=list)
    score: int = 0


def clean_text(value: Any) -> str:
    """Return compact plain text from API strings that may include simple markup."""
    if value is None:
        return ""
    if isinstance(value, list):
        value = " ".join(str(item) for item in value if item)
    text = str(value)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def normalize_doi(doi: str) -> str:
    doi = doi.strip().lower()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    return doi


def sentence_case_title(title: str) -> str:
    title = clean_text(title)
    if not title:
        return ""
    if title.isupper() or title.istitle():
        title = title.lower()
        return title[:1].upper() + title[1:]
    return title


def initials(given_name: str) -> str:
    parts = [part for part in re.split(r"[\s.-]+", given_name.strip()) if part]
    return " ".join(f"{part[0].upper()}." for part in parts)


def format_author_for_apa(author_name: str) -> str:
    """Best-effort APA author formatting from either 'Given Family' or raw name."""
    name = clean_text(author_name)
    if not name:
        return ""
    if "," in name:
        family, given = [piece.strip() for piece in name.split(",", 1)]
        return f"{family}, {initials(given)}".strip()
    parts = name.split()
    if len(parts) == 1:
        return parts[0]
    family = parts[-1]
    given = " ".join(parts[:-1])
    return f"{family}, {initials(given)}"


def format_authors_for_apa(authors: List[str]) -> str:
    formatted = [format_author_for_apa(author) for author in authors if author]
    formatted = [author for author in formatted if author]
    if not formatted:
        return "Unknown author"
    if len(formatted) == 1:
        return formatted[0]
    if len(formatted) <= 20:
        return ", ".join(formatted[:-1]) + f", & {formatted[-1]}"
    return ", ".join(formatted[:19]) + f", ... {formatted[-1]}"


def build_apa_citation(candidate: PaperCandidate) -> str:
    authors = format_authors_for_apa(candidate.authors)
    year = candidate.year or "n.d."
    title = sentence_case_title(candidate.title)
    venue = clean_text(candidate.journal_or_venue)
    doi_or_url = ""
    if candidate.doi:
        doi_or_url = f" https://doi.org/{normalize_doi(candidate.doi)}"
    elif candidate.url:
        doi_or_url = f" {candidate.url}"

    if venue:
        return f"{authors} ({year}). {title}. {venue}.{doi_or_url}".strip()
    return f"{authors} ({year}). {title}.{doi_or_url}".strip()


def build_queries() -> List[Tuple[str, str]]:
    """Build a compact set of public administration methodology searches."""
    queries: List[Tuple[str, str]] = []
    core_terms = PUBLIC_ADMIN_TERMS[:3]
    for category, method_terms in METHODOLOGY_SEARCH_TERMS.items():
        for method_term in method_terms[:4]:
            for core_term in core_terms:
                queries.append((category, f"{core_term} {method_term}"))
    return queries


def request_json(
    url: str,
    params: Dict[str, Any],
    headers: Dict[str, str],
    sleep_seconds: float,
    max_retries: int = 3,
) -> Optional[Dict[str, Any]]:
    """Fetch JSON with simple retry and rate-limit handling."""
    encoded_params = urllib.parse.urlencode(
        {key: value for key, value in params.items() if value not in (None, "")}
    )
    request_url = f"{url}?{encoded_params}"

    for attempt in range(1, max_retries + 1):
        try:
            time.sleep(sleep_seconds)
            request = urllib.request.Request(request_url, headers=headers)
            with urllib.request.urlopen(request, timeout=30) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return json.loads(response.read().decode(charset, errors="replace"))
        except urllib.error.HTTPError as exc:
            wait = sleep_seconds * (2**attempt)
            print(f"HTTP {exc.code} for {url}; retrying in {wait:.1f}s...")
            if exc.code in {429, 500, 502, 503, 504} and attempt < max_retries:
                time.sleep(wait)
                continue
            print(f"Skipping request after HTTP error: {exc}")
            return None
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            wait = sleep_seconds * (2**attempt)
            print(f"Request problem for {url}: {exc}; retrying in {wait:.1f}s...")
            if attempt < max_retries:
                time.sleep(wait)
                continue
            print(f"Skipping request after repeated errors: {exc}")
            return None

    return None


def crossref_headers() -> Dict[str, str]:
    user_agent = "ai-playbook-paper-finder/1.0"
    if CONTACT_EMAIL:
        user_agent += f" (mailto:{CONTACT_EMAIL})"
    return {"User-Agent": user_agent}


def semantic_scholar_headers() -> Dict[str, str]:
    return {"User-Agent": "ai-playbook-paper-finder/1.0"}


def extract_crossref_year(item: Dict[str, Any]) -> str:
    for key in ("published-print", "published-online", "published", "issued"):
        date_parts = item.get(key, {}).get("date-parts", [])
        if date_parts and date_parts[0]:
            return str(date_parts[0][0])
    return ""


def extract_crossref_authors(item: Dict[str, Any]) -> List[str]:
    authors = []
    for author in item.get("author", []) or []:
        family = clean_text(author.get("family"))
        given = clean_text(author.get("given"))
        if family and given:
            authors.append(f"{given} {family}")
        elif family:
            authors.append(family)
        elif given:
            authors.append(given)
    return authors


def crossref_to_candidate(
    item: Dict[str, Any],
    search_category: str,
) -> PaperCandidate:
    title = clean_text(item.get("title", [""])[0] if item.get("title") else "")
    journal = clean_text(
        item.get("container-title", [""])[0] if item.get("container-title") else ""
    )
    doi = normalize_doi(clean_text(item.get("DOI")))
    url = clean_text(item.get("URL"))
    abstract = clean_text(item.get("abstract"))

    candidate = PaperCandidate(
        title=title,
        authors=extract_crossref_authors(item),
        year=extract_crossref_year(item),
        journal_or_venue=journal,
        doi=doi,
        url=url,
        abstract=abstract,
        source_api="Crossref",
        search_category=search_category,
        publication_types=[clean_text(item.get("type")) or "journal-article"],
    )
    classify_candidate(candidate)
    candidate.apa_style_citation_draft = build_apa_citation(candidate)
    return candidate


def search_crossref(
    query: str,
    search_category: str,
    rows: int,
    start_year: int,
    sleep_seconds: float,
) -> List[PaperCandidate]:
    filters = f"type:journal-article,from-pub-date:{start_year}-01-01"
    params = {
        "query.bibliographic": query,
        "filter": filters,
        "rows": rows,
        "select": "title,author,issued,published,published-print,published-online,"
        "container-title,DOI,URL,abstract,type,subject",
        "sort": "relevance",
        "order": "desc",
        "mailto": CONTACT_EMAIL,
    }
    data = request_json(
        CROSSREF_API,
        params=params,
        headers=crossref_headers(),
        sleep_seconds=sleep_seconds,
    )
    if not data:
        return []

    items = data.get("message", {}).get("items", [])
    candidates = []
    for item in items:
        candidate = crossref_to_candidate(item, search_category)
        if candidate.title:
            candidates.append(candidate)
    return candidates


def semantic_to_candidate(
    item: Dict[str, Any],
    search_category: str,
) -> PaperCandidate:
    external_ids = item.get("externalIds") or {}
    doi = normalize_doi(clean_text(external_ids.get("DOI")))
    journal_info = item.get("journal") or {}
    journal_name = clean_text(journal_info.get("name"))
    venue = clean_text(item.get("venue")) or journal_name

    authors = []
    for author in item.get("authors", []) or []:
        name = clean_text(author.get("name"))
        if name:
            authors.append(name)

    candidate = PaperCandidate(
        title=clean_text(item.get("title")),
        authors=authors,
        year=str(item.get("year") or ""),
        journal_or_venue=venue,
        doi=doi,
        url=clean_text(item.get("url")),
        abstract=clean_text(item.get("abstract")),
        source_api="Semantic Scholar",
        search_category=search_category,
        publication_types=[
            clean_text(publication_type)
            for publication_type in (item.get("publicationTypes") or [])
            if clean_text(publication_type)
        ],
    )
    classify_candidate(candidate)
    candidate.apa_style_citation_draft = build_apa_citation(candidate)
    return candidate


def search_semantic_scholar(
    query: str,
    search_category: str,
    rows: int,
    start_year: int,
    sleep_seconds: float,
) -> List[PaperCandidate]:
    fields = ",".join(
        [
            "title",
            "authors",
            "year",
            "venue",
            "abstract",
            "externalIds",
            "url",
            "publicationTypes",
            "journal",
            "fieldsOfStudy",
        ]
    )
    params = {
        "query": query,
        "limit": min(rows, 100),
        "fields": fields,
        "year": f"{start_year}-",
    }
    data = request_json(
        SEMANTIC_SCHOLAR_API,
        params=params,
        headers=semantic_scholar_headers(),
        sleep_seconds=sleep_seconds,
    )
    if not data:
        return []

    items = data.get("data", [])
    candidates = []
    for item in items:
        candidate = semantic_to_candidate(item, search_category)
        if candidate.title:
            candidates.append(candidate)
    return candidates


def keyword_hits(text: str, keywords: Iterable[str]) -> List[str]:
    text_lower = text.lower()
    hits = []
    for keyword in keywords:
        pattern = r"\b" + re.escape(keyword.lower()).replace(r"\ ", r"\s+") + r"\b"
        if re.search(pattern, text_lower):
            hits.append(keyword)
    return hits


def classify_candidate(candidate: PaperCandidate) -> None:
    """Assign a methodology category with a transparent keyword justification."""
    searchable_text = " ".join(
        [
            candidate.title,
            candidate.abstract,
            candidate.journal_or_venue,
            candidate.search_category,
        ]
    )

    category_scores: Dict[str, Tuple[int, List[str]]] = {}
    for category, keywords in METHODOLOGY_KEYWORDS.items():
        hits = keyword_hits(searchable_text, keywords)
        category_scores[category] = (len(hits), hits)

    quantitative_score, quantitative_hits = category_scores["Quantitative"]
    qualitative_score, qualitative_hits = category_scores["Qualitative"]
    mixed_score, mixed_hits = category_scores["Mixed Methods"]
    if quantitative_score and qualitative_score:
        category_scores["Mixed Methods"] = (
            mixed_score + 2,
            mixed_hits
            + [f"{quantitative_hits[0]} plus {qualitative_hits[0]} indicators"],
        )

    best_category = candidate.search_category
    best_score, best_hits = category_scores.get(best_category, (0, []))
    for category, (score, hits) in category_scores.items():
        if score > best_score:
            best_category = category
            best_score = score
            best_hits = hits

    candidate.suggested_methodology_category = best_category
    candidate.score = best_score
    if best_hits:
        shown_hits = ", ".join(best_hits[:4])
        candidate.one_sentence_justification = (
            f"Classified as {best_category} because the metadata includes "
            f"methodology keyword(s): {shown_hits}."
        )
    else:
        candidate.one_sentence_justification = (
            f"Classified as {best_category} because it was returned by a "
            f"{candidate.search_category.lower()}-focused public administration search."
        )


def public_admin_relevance_score(candidate: PaperCandidate) -> int:
    text = " ".join([candidate.title, candidate.abstract, candidate.journal_or_venue])
    score = public_admin_domain_score(candidate)
    if candidate.abstract:
        score += 1
    if candidate.doi:
        score += 1
    return score


def public_admin_domain_score(candidate: PaperCandidate) -> int:
    text = " ".join([candidate.title, candidate.abstract, candidate.journal_or_venue])
    score = len(keyword_hits(text, PUBLIC_ADMIN_KEYWORDS))
    venue = candidate.journal_or_venue.lower()
    if any(hint in venue for hint in JOURNAL_HINTS):
        score += 3
    return score


def is_likely_relevant(candidate: PaperCandidate) -> bool:
    if not candidate.title:
        return False
    if candidate.source_api == "Semantic Scholar" and candidate.publication_types:
        peer_review_like = {"journalarticle", "review"}
        normalized_types = {
            re.sub(r"[^a-z]", "", publication_type.lower())
            for publication_type in candidate.publication_types
        }
        if not normalized_types.intersection(peer_review_like):
            return False
    return public_admin_domain_score(candidate) >= 1


def deduplicate(candidates: Iterable[PaperCandidate]) -> List[PaperCandidate]:
    seen: Dict[str, PaperCandidate] = {}

    for candidate in candidates:
        key = ""
        if candidate.doi:
            key = f"doi:{normalize_doi(candidate.doi)}"
        else:
            key = f"title:{normalize_title(candidate.title)}"

        existing = seen.get(key)
        if existing is None:
            seen[key] = candidate
            continue

        # Keep the richer metadata record when duplicate records are found.
        existing_richness = sum(
            bool(value)
            for value in [
                existing.abstract,
                existing.doi,
                existing.url,
                existing.journal_or_venue,
                existing.authors,
            ]
        )
        candidate_richness = sum(
            bool(value)
            for value in [
                candidate.abstract,
                candidate.doi,
                candidate.url,
                candidate.journal_or_venue,
                candidate.authors,
            ]
        )
        if candidate_richness > existing_richness:
            seen[key] = candidate

    return list(seen.values())


def select_balanced_candidates(
    candidates: List[PaperCandidate],
    target_per_category: int,
) -> List[PaperCandidate]:
    ranked = sorted(
        candidates,
        key=lambda item: (
            item.suggested_methodology_category,
            -item.score,
            -public_admin_relevance_score(item),
            item.year or "0000",
            item.title,
        ),
    )

    selected: List[PaperCandidate] = []
    counts = {category: 0 for category in METHODOLOGY_SEARCH_TERMS}
    for candidate in ranked:
        category = candidate.suggested_methodology_category
        if counts.get(category, 0) < target_per_category:
            selected.append(candidate)
            counts[category] = counts.get(category, 0) + 1

    # Include overflow only when a category has no hits and the record came from
    # that search tradition. This keeps the report useful even when metadata is
    # sparse.
    for category in METHODOLOGY_SEARCH_TERMS:
        if counts.get(category, 0) > 0:
            continue
        fallback = [
            item
            for item in candidates
            if item.search_category == category and item not in selected
        ]
        fallback.sort(
            key=lambda item: (-public_admin_relevance_score(item), item.title)
        )
        for candidate in fallback[:target_per_category]:
            candidate.suggested_methodology_category = category
            candidate.score = max(candidate.score, 1)
            candidate.one_sentence_justification = (
                f"Included as {category} because it was returned by a "
                f"{category.lower()}-focused public administration search; "
                "verify the methods section before final selection."
            )
            candidate.apa_style_citation_draft = build_apa_citation(candidate)
            selected.append(candidate)
            counts[category] = counts.get(category, 0) + 1

    selected.sort(
        key=lambda item: (
            item.suggested_methodology_category,
            -item.score,
            -public_admin_relevance_score(item),
            item.title,
        )
    )
    return selected


def candidate_to_row(candidate: PaperCandidate) -> Dict[str, str]:
    return {
        "title": candidate.title,
        "authors": "; ".join(candidate.authors),
        "year": candidate.year,
        "journal_or_venue": candidate.journal_or_venue,
        "doi": candidate.doi,
        "url": candidate.url,
        "abstract": candidate.abstract,
        "suggested_methodology_category": candidate.suggested_methodology_category,
        "one_sentence_justification": candidate.one_sentence_justification,
        "apa_style_citation_draft": candidate.apa_style_citation_draft,
        "source_api": candidate.source_api,
        "search_category": candidate.search_category,
        "publication_types": "; ".join(candidate.publication_types),
        "metadata_score": str(candidate.score),
    }


def write_csv(candidates: List[PaperCandidate], path: str) -> None:
    fieldnames = list(candidate_to_row(PaperCandidate(title="")).keys())
    with open(path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for candidate in candidates:
            writer.writerow(candidate_to_row(candidate))


def markdown_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def truncate(text: str, max_chars: int = 700) -> str:
    text = clean_text(text)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def write_report(
    candidates: List[PaperCandidate],
    path: str,
    args: argparse.Namespace,
) -> None:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    by_category: Dict[str, List[PaperCandidate]] = {
        category: [] for category in METHODOLOGY_SEARCH_TERMS
    }
    for candidate in candidates:
        by_category.setdefault(candidate.suggested_methodology_category, []).append(
            candidate
        )

    lines = [
        "# AI Playbook Paper Finder Report",
        "",
        f"Generated: {generated_at}",
        "",
        "## Purpose",
        "",
        (
            "This report lists candidate peer-reviewed research papers for "
            "Assignment 3: 7-Paper Pilot & Fidelity Assessment. Treat the "
            "methodology categories as suggestions: verify each paper's full "
            "text, methods section, journal status, and fit before final use."
        ),
        "",
        "## Search Settings",
        "",
        f"- Sources: Crossref REST API and Semantic Scholar Graph API",
        f"- Start year: {args.start_year}",
        f"- Rows per query per source: {args.rows_per_query}",
        f"- Target candidates per category: {args.target_per_category}",
        f"- Rate-limit sleep: {args.sleep_seconds:.1f} seconds/request",
        "",
        "## Category Counts",
        "",
        "| Methodology | Candidates |",
        "|---|---:|",
    ]

    for category in METHODOLOGY_SEARCH_TERMS:
        lines.append(f"| {category} | {len(by_category.get(category, []))} |")

    lines.extend(
        [
            "",
            "## Candidates by Methodology",
            "",
        ]
    )

    for category in METHODOLOGY_SEARCH_TERMS:
        lines.append(f"### {category}")
        lines.append("")
        category_candidates = by_category.get(category, [])
        if not category_candidates:
            lines.append("_No candidates found for this category._")
            lines.append("")
            continue

        for index, candidate in enumerate(category_candidates, start=1):
            doi_or_url = (
                f"https://doi.org/{normalize_doi(candidate.doi)}"
                if candidate.doi
                else candidate.url
            )
            lines.extend(
                [
                    f"#### {index}. {candidate.title}",
                    "",
                    f"- Authors: {', '.join(candidate.authors) or 'Unknown'}",
                    f"- Year: {candidate.year or 'Unknown'}",
                    f"- Journal/Venue: {candidate.journal_or_venue or 'Unknown'}",
                    f"- DOI: {candidate.doi or 'Not available'}",
                    f"- URL: {doi_or_url or 'Not available'}",
                    f"- Source API: {candidate.source_api}",
                    f"- Suggested methodology: {candidate.suggested_methodology_category}",
                    f"- Justification: {candidate.one_sentence_justification}",
                    f"- APA draft: {candidate.apa_style_citation_draft}",
                    "",
                    "**Abstract/summary from metadata:**",
                    "",
                    truncate(candidate.abstract) or "_No abstract available in metadata._",
                    "",
                ]
            )

    lines.extend(
        [
            "## Next-Step Fidelity Checks",
            "",
            "- Confirm that each selected paper is peer reviewed and belongs to a suitable public administration, public policy, or related journal.",
            "- Read the methods section before final categorization; keyword classification can mislabel conceptual, review, or empirical papers.",
            "- Replace any incomplete APA citation drafts with final APA 7 formatting from the article PDF or journal page.",
            "- For the 7-paper pilot, choose one strong paper from each methodology category and document why it is a high-fidelity example.",
            "",
        ]
    )

    with open(path, "w", encoding="utf-8") as md_file:
        md_file.write("\n".join(lines))


def print_summary(candidates: List[PaperCandidate]) -> None:
    print("\nSearch complete.")
    print(f"Exported {len(candidates)} candidate records.")
    for category in METHODOLOGY_SEARCH_TERMS:
        count = sum(
            1
            for candidate in candidates
            if candidate.suggested_methodology_category == category
        )
        print(f"  {category}: {count}")
    print(f"\nFiles written:\n  {OUTPUT_CSV}\n  {OUTPUT_MD}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Find public administration/public policy paper candidates across "
            "seven methodological traditions using public scholarly metadata APIs."
        )
    )
    parser.add_argument(
        "--rows-per-query",
        type=int,
        default=DEFAULT_ROWS_PER_QUERY,
        help=f"Rows to request per query from each API. Default: {DEFAULT_ROWS_PER_QUERY}",
    )
    parser.add_argument(
        "--target-per-category",
        type=int,
        default=DEFAULT_TARGET_PER_CATEGORY,
        help=(
            "Maximum candidates to keep per suggested methodology category. "
            f"Default: {DEFAULT_TARGET_PER_CATEGORY}"
        ),
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=DEFAULT_START_YEAR,
        help=f"Only request papers from this year onward. Default: {DEFAULT_START_YEAR}",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=DEFAULT_SLEEP_SECONDS,
        help=(
            "Seconds to sleep before each API request for rate limiting. "
            f"Default: {DEFAULT_SLEEP_SECONDS}"
        ),
    )
    parser.add_argument(
        "--semantic-only",
        action="store_true",
        help="Search only Semantic Scholar.",
    )
    parser.add_argument(
        "--crossref-only",
        action="store_true",
        help="Search only Crossref.",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.rows_per_query < 1:
        raise ValueError("--rows-per-query must be at least 1")
    if args.target_per_category < 1:
        raise ValueError("--target-per-category must be at least 1")
    if args.start_year < 1900 or args.start_year > datetime.now().year:
        raise ValueError("--start-year must be between 1900 and the current year")
    if args.sleep_seconds < 0:
        raise ValueError("--sleep-seconds cannot be negative")
    if args.semantic_only and args.crossref_only:
        raise ValueError("Choose either --semantic-only or --crossref-only, not both")


def run_search(args: argparse.Namespace) -> List[PaperCandidate]:
    queries = build_queries()
    all_candidates: List[PaperCandidate] = []

    print("Starting paper search...")
    print(f"Queries: {len(queries)}")
    print("This may take a few minutes because the script pauses between requests.\n")

    for index, (category, query) in enumerate(queries, start=1):
        print(f"[{index}/{len(queries)}] {category}: {query}")

        if not args.semantic_only:
            crossref_results = search_crossref(
                query=query,
                search_category=category,
                rows=args.rows_per_query,
                start_year=args.start_year,
                sleep_seconds=args.sleep_seconds,
            )
            all_candidates.extend(crossref_results)
            print(f"  Crossref: {len(crossref_results)}")

        if not args.crossref_only:
            semantic_results = search_semantic_scholar(
                query=query,
                search_category=category,
                rows=args.rows_per_query,
                start_year=args.start_year,
                sleep_seconds=args.sleep_seconds,
            )
            all_candidates.extend(semantic_results)
            print(f"  Semantic Scholar: {len(semantic_results)}")

    print("\nFiltering and deduplicating results...")
    relevant = [candidate for candidate in all_candidates if is_likely_relevant(candidate)]
    deduped = deduplicate(relevant)
    selected = select_balanced_candidates(deduped, args.target_per_category)

    for candidate in selected:
        candidate.apa_style_citation_draft = build_apa_citation(candidate)

    return selected


def main() -> int:
    try:
        args = parse_args()
        validate_args(args)
        candidates = run_search(args)
        write_csv(candidates, OUTPUT_CSV)
        write_report(candidates, OUTPUT_MD, args)
        print_summary(candidates)
        return 0
    except KeyboardInterrupt:
        print("\nSearch cancelled by user.")
        return 130
    except Exception as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
