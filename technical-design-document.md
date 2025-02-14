# rss-pipes: Composable RSS feeds utilities, inspired by unix pipes**

## Rationale

RSS feeds provide a structured way to consume content, but they often suffer from excessive noise and overwhelming volume. Users seeking a more manageable way to stay informed would benefit from tools that allow them to:

1. **Aggregate and filter content** – Creating periodic digests to reduce noise.
2. **Summarise lengthy feeds** – Condensing content to make it more digestible.
3. **Chain tools together** – Combining filtering and summarisation for maximum usability.

By providing an RSS digest service and a summarisation service, users can efficiently consume content without getting lost in excessive information.

## Design Overview

The system will be developed as a single service with two endpoints:

1. **RSS Digest Endpoint** – Aggregates and compiles RSS feeds into periodic digests (e.g., daily, weekly, monthly), controlled via a query parameter.
2. **RSS Summarisation Endpoint** – Summarises the content of RSS entries using AI-powered text compression.

Both endpoints will expose RESTful APIs, allowing users to pipe one endpoint’s output into another seamlessly. Endpoints will pass through query parameters they do not use.

### Example Workflow

1. Convert a noisy RSS feed into a weekly digest:
   ```
   https://rss-tools.com/digest/https://noisy.com/feed.atom&period=weekly
   ```
2. Summarise the generated digest:
   ```
   https://rss-tools.com/summarise/https://rss-tools.com/digest?feed=https://noisy.com/feed.atom&period=weekly
   ```

This composability ensures users can tailor their RSS consumption to their preferences.

## Technical Overview

- **FastAPI** – Lightweight, high-performance web framework for building RESTful APIs.
- **Docker** – Containerised deployment for scalability and portability.
- **LiteLLM** – Used to select the **Gemini 2.0 Flash** model for cost-effective AI-based summarisation while remaining under the free quota.
- **Python feedparser** – Used for parsing and manipulating RSS feeds.
- **Database for Persistent Caching** – Summaries are stored in a database, ensuring that future summarisation requests retrieve pre-existing summaries rather than reprocessing the same content.
- **uv** – Used for package management.
- **OpenTelemetry (Otel)** – Auto-instrumentation for observability.
- **Grafana Cloud** – Centralised monitoring and performance tracking.
