# RSS-Pipes

Composable RSS feed utilities inspired by Unix pipes. RSS-Pipes lets you transform, aggregate and filter RSS/Atom feeds via simple RESTful endpoints—so you can build custom digests or connect multiple tools in a pipeline.

---

## Features

- **Digest Generation**
  Aggregate feed entries into daily, weekly, or monthly digests.

- **Flexible Scheduling**
  Use human-readable schedule strings (`daily-HH:MM`, `weekly-{mon|tue|…|sun}-HH:MM`, `monthly-{day}-HH:MM`).

- **Composable**
  Pipe one endpoint's URL into another (e.g. digest → summarise).

---

## Quickstart

### Requirements

- Python 3.13 or later
- [uv](https://pypi.org/project/uv/) (development runner)

### Installation

```bash
git clone https://github.com/your-org/rss-pipes.git
cd rss-pipes
uv install
```

### Run the API

```bash
uv run fastapi dev rss_pipes/main.py
```

The service will start on `http://localhost:8000`.

---

## Usage

### Digest Endpoint

Generate an Atom digest by hitting the `/digest/{feed_url}` endpoint:

```
GET /digest/{feed_url:path}?schedule={schedule}
```

- **feed_url**: URL to an RSS/Atom feed
- **schedule**: schedule string, e.g.:
  - `daily-09:00`
  - `weekly-sat-10:00`
  - `monthly-15-09:00`

Example:

```bash
curl \
  --get \
  --data-urlencode "schedule=weekly-sat-10:00" \
  http://127.0.0.1:8000/digest/https://leverstone.me/blog/atom.xml
```

**Response**: A new feed, digested following the provided schedule.

### Schedule Format

| Type    | Syntax                | Description                           |
| ------- | --------------------- | ------------------------------------- |
| Daily   | `daily-HH:MM`         | Every day at hour:minute             |
| Weekly  | `weekly-<day>-HH:MM`  | Every week on `<day>` at time        |
| Monthly | `monthly-<day>-HH:MM` | Every month on day `<day>` at time   |

Valid days for weekly: `mon`, `tue`, `wed`, `thu`, `fri`, `sat`, `sun`.

Valid days for monthly: `1` to `31`. For months shorter than the specified day, the occurrence will be on the last day of that month.

---

## Deployment

### Dokku Deployment

This project is configured for deployment to Dokku instances:

1. **Add your Dokku remote**:
   ```bash
   git remote add dokku dokku@your-server:rss-pipes
   ```

2. **Deploy**:
   ```bash
   git push dokku main
   ```

Dokku will automatically detect the Dockerfile and deploy the application.

---

## Development

We use [uv](https://pypi.org/project/uv/) as a task runner:

- **Run tests**
  `uv run python -m pytest`

- **Lint**
  `uv run ruff check`
  `uv run ruff format --check`

- **Autoformat**
  `uv run ruff format`
  `uv run ruff check --fix`

- **Type check**
  `uv run mypy .`
