from typing import Annotated

import httpx
from fastapi import FastAPI, HTTPException, Query, Request

from .digest import FeedParsingError, digest_feed
from .schedule import Schedule

app = FastAPI()


@app.exception_handler(httpx.HTTPStatusError)
async def httpx_handler(request: Request, exc: httpx.HTTPStatusError):
    raise HTTPException(
        status_code=exc.response.status_code,
        detail=str(exc),
    )


@app.exception_handler(FeedParsingError)
async def feed_parsing_handler(request: Request, exc: FeedParsingError):
    raise HTTPException(
        status_code=400,
        detail=str(exc),
    )


@app.get("/digest/{feed_url:path}")
async def digest(
    schedule_str: Annotated[str, Query(alias="schedule")],
    feed_url: str,
):
    """
    Create a digest of RSS feed entries for the specified period.
    """
    try:
        schedule = Schedule.validate(schedule_str)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return await digest_feed(feed_url, schedule)
