import os
from datetime import datetime
from typing import NotRequired, TypedDict
from urllib.parse import urljoin, urlparse, urlunparse

import feedparser  # type: ignore
import httpx
from bs4 import BeautifulSoup
from bs4.element import Tag
from jinja2 import Environment, FileSystemLoader

from .schedule import Schedule, apply_schedule


class FeedParsingError(ValueError):
    def __init__(self, message):
        super().__init__(message)


class EntryData(TypedDict):
    title: str
    link: str
    content: str
    published: NotRequired[str]
    updated: NotRequired[str]


class DigestEntry(TypedDict):
    date: datetime
    entries: list[EntryData]


class TemplateContext(TypedDict):
    authors: set[str]
    frequency: str
    digests: list[DigestEntry]
    title: NotRequired[str]
    link: NotRequired[str]
    id: NotRequired[str]
    updated: NotRequired[datetime]


def dt_isoformat(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def dt_readable_date(dt: datetime) -> str:
    return dt.strftime("%d %b %Y")


# Initialize Jinja2 environment
template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)
jinja_env.filters["dt_isoformat"] = dt_isoformat
jinja_env.filters["dt_readable_date"] = dt_readable_date


async def digest_feed(feed_url: str, schedule: Schedule):
    """Fetch an RSS/Atom feed and generate a digest feed based on the given schedule."""
    feed = await _fetch_feed(feed_url)
    base_url = _get_base_url(feed_url)
    template_context = _prepare_template_context(schedule, feed, base_url)
    template = jinja_env.get_template("atom.xml.jinja2")
    return template.render(**template_context)


def _prepare_template_context(
    schedule: Schedule, feed, base_url: str | None
) -> TemplateContext:
    authors = _extract_authors(feed)
    items = _extract_datetime_entry_pairs(feed)

    # Apply schedule to get digests
    digests = []
    for occurrence, period_items in apply_schedule(schedule, items):
        # Sort items by date (newest first)
        sorted_items = sorted(period_items, key=lambda x: x[0], reverse=True)

        # Create the digest entry
        digest_entry: DigestEntry = {
            "date": occurrence,
            "entries": [_extract_entry_data(e, base_url) for _, e in sorted_items],
        }
        digests.append((occurrence, digest_entry))

    # Sort digests by date (newest first)
    digests.sort(key=lambda x: x[0], reverse=True)

    context: TemplateContext = {
        "authors": authors,
        "frequency": schedule.frequency.value,
        "digests": [digest for _, digest in digests],
    }

    for field in "title", "link", "id":
        if hasattr(feed.feed, field):
            context[field] = getattr(feed.feed, field)

    if digests:
        context["updated"] = digests[0][0]

    return context


async def _fetch_feed(feed_url):
    async with httpx.AsyncClient() as client:
        r = await client.get(feed_url)
        r.raise_for_status()

    feed = feedparser.parse(r.text)

    if feed.bozo:  # feedparser sets this flag for malformed feeds
        raise FeedParsingError(f"Invalid or malformed feed: {feed.bozo_exception}")
    return feed


def _extract_authors(feed) -> set[str]:
    authors = set()
    if hasattr(feed.feed, "author"):
        authors.add(feed.feed.author)
    for entry in feed.entries:
        if hasattr(entry, "author"):
            authors.add(entry.author)
    return authors


def _extract_datetime_entry_pairs(feed):
    items = []
    for entry in feed.entries:
        # Use published date if available, otherwise use updated date
        entry_time = None
        if hasattr(entry, "published"):
            entry_time = datetime.fromisoformat(entry.published)
        elif hasattr(entry, "updated"):
            entry_time = datetime.fromisoformat(entry.updated)

        if entry_time:
            items.append((entry_time, entry))
    return items


def _extract_entry_data(entry, base_url: str | None) -> EntryData:
    # Get content or summary
    item_content = ""
    if hasattr(entry, "content") and entry.content:
        item_content = entry.content[0].value
    elif hasattr(entry, "summary"):
        item_content = entry.summary

    if base_url:
        item_content = _rewrite_relative_urls(item_content, base_url)
        link = urljoin(base_url, entry.link)
    else:
        link = entry.link

    # Extract raw data for template
    entry_data: EntryData = {
        "title": entry.title,
        "link": link,
        "content": item_content,
    }

    # Add date information
    if hasattr(entry, "published"):
        entry_data["published"] = entry.published
    elif hasattr(entry, "updated"):
        entry_data["updated"] = entry.updated

    return entry_data


def _rewrite_relative_urls(html: str, base_url: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for attr in ["src", "href"]:
        for tag in soup.find_all(attrs={attr: True}):
            if not isinstance(tag, Tag):
                continue
            val = tag[attr]
            if isinstance(val, str) and not val.startswith(
                ("http://", "https://", "//")
            ):
                tag[attr] = urljoin(base_url, val)
    return str(soup)


def _get_base_url(absolute_url: str) -> str | None:
    parsed_url = urlparse(absolute_url)

    if parsed_url.scheme and parsed_url.netloc:
        # Replace all but scheme and netloc
        base_url_parts = parsed_url._replace(path="", params="", query="", fragment="")
        return urlunparse(base_url_parts)
    return None
