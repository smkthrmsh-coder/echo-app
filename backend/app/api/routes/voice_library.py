"""
Voice library endpoint — celebrity voices organized by profession category.
Fetches live from ElevenLabs when voices_read permission is available (paid plan).
Falls back to curated hand-picked voices that match each category's energy.
"""

import time
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# 10 celebrity profession categories
# ---------------------------------------------------------------------------

CATEGORIES = [
    {
        "id": "actors",
        "label": "Actors",
        "emoji": "🎬",
        "description": "Hollywood & TV actors",
        "el_search": "actor cinema dramatic",
        "el_category": "entertainment",
    },
    {
        "id": "musicians",
        "label": "Musicians",
        "emoji": "🎵",
        "description": "Singers & music artists",
        "el_search": "singer musician artist",
        "el_category": "entertainment",
    },
    {
        "id": "athletes",
        "label": "Athletes",
        "emoji": "🏆",
        "description": "Sports stars & commentators",
        "el_search": "sports athlete energetic",
        "el_category": "sports_commentary",
    },
    {
        "id": "comedians",
        "label": "Comedians",
        "emoji": "😂",
        "description": "Stand-up comedians & comedy personalities",
        "el_search": "comedy funny casual",
        "el_category": "entertainment",
    },
    {
        "id": "tv_hosts",
        "label": "TV & Talk Shows",
        "emoji": "📺",
        "description": "Talk show hosts & TV presenters",
        "el_search": "talk show host presenter",
        "el_category": "news_presenter",
    },
    {
        "id": "podcasters",
        "label": "Podcasters",
        "emoji": "🎙",
        "description": "Famous podcasters & creators",
        "el_search": "podcast creator conversational",
        "el_category": "social_media",
    },
    {
        "id": "business",
        "label": "Business & Tech",
        "emoji": "💼",
        "description": "Entrepreneurs & industry leaders",
        "el_search": "business professional authoritative",
        "el_category": "news_presenter",
    },
    {
        "id": "gaming",
        "label": "Streamers & Gaming",
        "emoji": "🎮",
        "description": "Gaming personalities & streamers",
        "el_search": "gaming streamer energetic",
        "el_category": "gaming",
    },
    {
        "id": "history",
        "label": "Historical Figures",
        "emoji": "🌍",
        "description": "World leaders, icons & historical voices",
        "el_search": "historical leader iconic",
        "el_category": "characters",
    },
    {
        "id": "wellness",
        "label": "Wellness & Coaches",
        "emoji": "🌟",
        "description": "Motivational speakers & life coaches",
        "el_search": "motivational wellness coach",
        "el_category": "meditation",
    },
]

CATEGORY_MAP = {c["id"]: c for c in CATEGORIES}

# ---------------------------------------------------------------------------
# Curated fallback: voices that match each celebrity category's energy.
# Shown when voices_read permission is missing (free plan).
# Real celebrity voices from ElevenLabs library unlock with a paid plan.
# ---------------------------------------------------------------------------

CURATED_VOICES: dict[str, list[dict]] = {
    "actors": [
        {"voice_id": "JBFqnCBsd6RMkjVDRZzb", "name": "George", "gender": "male", "accent": "British", "description": "Deep, dramatic, cinematic gravitas"},
        {"voice_id": "VR6AewLTigWG4xSOukaG", "name": "Arnold", "gender": "male", "accent": "American", "description": "Powerful, commanding screen presence"},
        {"voice_id": "jsCqWAovK2LkecY7zXl4", "name": "Freya", "gender": "female", "accent": "American", "description": "Rich, emotional, leading-lady energy"},
        {"voice_id": "Zlb1dXrM653N07WRdFW3", "name": "Joseph", "gender": "male", "accent": "British", "description": "Sophisticated British character actor"},
        {"voice_id": "ThT5KcBeYPX3keUQqHPh", "name": "Dorothy", "gender": "female", "accent": "British", "description": "Classic, expressive, theatrical"},
        {"voice_id": "MF3mGyEYCl7XYWbV9V6O", "name": "Elli", "gender": "female", "accent": "American", "description": "Emotional range, expressive delivery"},
    ],
    "musicians": [
        {"voice_id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella", "gender": "female", "accent": "American", "description": "Melodic, emotive, soulful tone"},
        {"voice_id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi", "gender": "female", "accent": "American", "description": "Bold, energetic pop artist energy"},
        {"voice_id": "zrHiDhphv9ZnVXBqCLjz", "name": "Mimi", "gender": "female", "accent": "Swedish/English", "description": "Unique timbre, artistic personality"},
        {"voice_id": "yoZ06aMxZJJ28mfd3POQ", "name": "Sam", "gender": "male", "accent": "American", "description": "Raspy, soulful, rock artist vibe"},
        {"voice_id": "TxGEqnHWrfWFTfGW9XjX", "name": "Josh", "gender": "male", "accent": "American", "description": "Smooth, melodic, R&B warmth"},
        {"voice_id": "pFZP5JQG7iQjIQuC4Bku", "name": "Lily", "gender": "female", "accent": "British", "description": "Elegant, lyrical, pop star presence"},
    ],
    "athletes": [
        {"voice_id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi", "gender": "female", "accent": "American", "description": "Fierce, competitive, game-day energy"},
        {"voice_id": "VR6AewLTigWG4xSOukaG", "name": "Arnold", "gender": "male", "accent": "American", "description": "Powerhouse, champion mentality"},
        {"voice_id": "wViXBPUzp2ZZixB1xQuM", "name": "Ryan", "gender": "male", "accent": "American", "description": "Athletic, upbeat, motivating"},
        {"voice_id": "SOYHLrjzK2X1ezoPC9cr", "name": "Harry", "gender": "male", "accent": "American", "description": "High-energy, intense, driven"},
        {"voice_id": "TX3LPaxmHKxFdv7VOFE1", "name": "Liam", "gender": "male", "accent": "American", "description": "Confident, inspiring, team-captain"},
        {"voice_id": "ODq5zmih8GrVes37Dx0d", "name": "Patrick", "gender": "male", "accent": "American", "description": "Commanding, champion presence"},
    ],
    "comedians": [
        {"voice_id": "IKne3meq5aSn9XLyUdCD", "name": "Charlie", "gender": "male", "accent": "Australian", "description": "Casual, witty, stand-up energy"},
        {"voice_id": "bVMeCyTHy58xNoL34h3p", "name": "Jeremy", "gender": "male", "accent": "American", "description": "Lively, humorous, comedic timing"},
        {"voice_id": "ErXwobaYiN019PkySvjV", "name": "Antoni", "gender": "male", "accent": "American", "description": "Charming, playful, crowd pleaser"},
        {"voice_id": "bIHbv24MWmeRgasZH58o", "name": "Will", "gender": "male", "accent": "American", "description": "Friendly, fun, quick wit"},
        {"voice_id": "zrHiDhphv9ZnVXBqCLjz", "name": "Mimi", "gender": "female", "accent": "Swedish/English", "description": "Quirky, offbeat, unique comedy style"},
        {"voice_id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi", "gender": "female", "accent": "American", "description": "Sharp, bold, confident humor"},
    ],
    "tv_hosts": [
        {"voice_id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "gender": "female", "accent": "American", "description": "Warm, polished, talk show presence"},
        {"voice_id": "JBFqnCBsd6RMkjVDRZzb", "name": "George", "gender": "male", "accent": "British", "description": "Authoritative British presenter"},
        {"voice_id": "flq6f7UD9byGKBbTKkKm", "name": "Michael", "gender": "male", "accent": "American", "description": "Smooth, professional, anchor energy"},
        {"voice_id": "cgSgspJ2msm6clMCkdW9", "name": "Jessica", "gender": "female", "accent": "American", "description": "Engaging, vibrant, screen presence"},
        {"voice_id": "pMsXgVXv3BLzUgSXRplE", "name": "Serena", "gender": "female", "accent": "American", "description": "Composed, sophisticated, anchor"},
        {"voice_id": "TX3LPaxmHKxFdv7VOFE1", "name": "Liam", "gender": "male", "accent": "American", "description": "Friendly, warm, talk show host"},
    ],
    "podcasters": [
        {"voice_id": "TxGEqnHWrfWFTfGW9XjX", "name": "Josh", "gender": "male", "accent": "American", "description": "Deep, long-form conversational"},
        {"voice_id": "IKne3meq5aSn9XLyUdCD", "name": "Charlie", "gender": "male", "accent": "Australian", "description": "Casual, curious, long-form storyteller"},
        {"voice_id": "bIHbv24MWmeRgasZH58o", "name": "Will", "gender": "male", "accent": "American", "description": "Friendly, thoughtful, interview style"},
        {"voice_id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "gender": "female", "accent": "American", "description": "Engaging, intelligent, podcast host"},
        {"voice_id": "ErXwobaYiN019PkySvjV", "name": "Antoni", "gender": "male", "accent": "American", "description": "Smooth, well-rounded, interview energy"},
        {"voice_id": "XrExE9yKIg1WjnnlVkGX", "name": "Matilda", "gender": "female", "accent": "American", "description": "Warm, narrative, storytelling podcast"},
    ],
    "business": [
        {"voice_id": "pNInz6obpgDQGcFmaJgB", "name": "Adam", "gender": "male", "accent": "American", "description": "Deep, commanding, CEO presence"},
        {"voice_id": "JBFqnCBsd6RMkjVDRZzb", "name": "George", "gender": "male", "accent": "British", "description": "Authoritative, strategic, boardroom"},
        {"voice_id": "flq6f7UD9byGKBbTKkKm", "name": "Michael", "gender": "male", "accent": "American", "description": "Clear, confident, executive voice"},
        {"voice_id": "pMsXgVXv3BLzUgSXRplE", "name": "Serena", "gender": "female", "accent": "American", "description": "Sharp, composed, C-suite presence"},
        {"voice_id": "Zlb1dXrM653N07WRdFW3", "name": "Joseph", "gender": "male", "accent": "British", "description": "Sophisticated, visionary, thought leader"},
        {"voice_id": "wViXBPUzp2ZZixB1xQuM", "name": "Ryan", "gender": "male", "accent": "American", "description": "Energetic entrepreneur, startup energy"},
    ],
    "gaming": [
        {"voice_id": "SOYHLrjzK2X1ezoPC9cr", "name": "Harry", "gender": "male", "accent": "American", "description": "High-energy streamer, live reaction"},
        {"voice_id": "yoZ06aMxZJJ28mfd3POQ", "name": "Sam", "gender": "male", "accent": "American", "description": "Raspy, dramatic, boss-fight narrator"},
        {"voice_id": "VR6AewLTigWG4xSOukaG", "name": "Arnold", "gender": "male", "accent": "American", "description": "Powerful, epic game trailer energy"},
        {"voice_id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi", "gender": "female", "accent": "American", "description": "Fierce, competitive, female pro gamer"},
        {"voice_id": "ODq5zmih8GrVes37Dx0d", "name": "Patrick", "gender": "male", "accent": "American", "description": "Epic, intense, cinematic game VO"},
        {"voice_id": "bVMeCyTHy58xNoL34h3p", "name": "Jeremy", "gender": "male", "accent": "American", "description": "Upbeat, hype, Twitch streamer energy"},
    ],
    "history": [
        {"voice_id": "JBFqnCBsd6RMkjVDRZzb", "name": "George", "gender": "male", "accent": "British", "description": "Stately, commanding, world leader"},
        {"voice_id": "pNInz6obpgDQGcFmaJgB", "name": "Adam", "gender": "male", "accent": "American", "description": "Deep, resonant, presidential gravitas"},
        {"voice_id": "Zlb1dXrM653N07WRdFW3", "name": "Joseph", "gender": "male", "accent": "British", "description": "Regal, distinguished, statesman"},
        {"voice_id": "ZQe5CZNOzWyzPSCn5a3c", "name": "James", "gender": "male", "accent": "Australian", "description": "Measured, authoritative, historic"},
        {"voice_id": "ThT5KcBeYPX3keUQqHPh", "name": "Dorothy", "gender": "female", "accent": "British", "description": "Iconic, dignified, historic voice"},
        {"voice_id": "flq6f7UD9byGKBbTKkKm", "name": "Michael", "gender": "male", "accent": "American", "description": "Powerful, prophetic, iconic delivery"},
    ],
    "wellness": [
        {"voice_id": "piTKgcLEGmPE4e6mEKli", "name": "Nicole", "gender": "female", "accent": "American", "description": "Soft, mindful, ASMR wellness guide"},
        {"voice_id": "oWAxZDx7w5VEj9dCyTzz", "name": "Grace", "gender": "female", "accent": "Southern US", "description": "Warm, nurturing, life coach energy"},
        {"voice_id": "TX3LPaxmHKxFdv7VOFE1", "name": "Liam", "gender": "male", "accent": "American", "description": "Inspiring, grounded, motivational"},
        {"voice_id": "pMsXgVXv3BLzUgSXRplE", "name": "Serena", "gender": "female", "accent": "American", "description": "Serene, wise, mindfulness teacher"},
        {"voice_id": "XrExE9yKIg1WjnnlVkGX", "name": "Matilda", "gender": "female", "accent": "American", "description": "Warm, encouraging, self-help guide"},
        {"voice_id": "wViXBPUzp2ZZixB1xQuM", "name": "Ryan", "gender": "male", "accent": "American", "description": "Energetic, positive, life coach"},
    ],
}

# ---------------------------------------------------------------------------
# Simple in-process cache
# ---------------------------------------------------------------------------
_cache: dict[str, tuple[float, list[dict]]] = {}
CACHE_TTL = 60 * 60 * 6  # 6 hours


class VoiceItem(BaseModel):
    voice_id: str
    name: str
    gender: str | None = None
    accent: str | None = None
    age: str | None = None
    description: str | None = None
    preview_url: str | None = None
    category: str | None = None


class CategoryInfo(BaseModel):
    id: str
    label: str
    emoji: str
    description: str


class VoiceLibraryResponse(BaseModel):
    category: CategoryInfo
    voices: list[VoiceItem]
    total: int
    note: str | None = None
    is_curated: bool = False


class CategoriesResponse(BaseModel):
    categories: list[CategoryInfo]


@router.get("/voices/categories", response_model=CategoriesResponse, tags=["voices"])
async def list_categories() -> CategoriesResponse:
    return CategoriesResponse(
        categories=[
            CategoryInfo(id=c["id"], label=c["label"], emoji=c["emoji"], description=c["description"])
            for c in CATEGORIES
        ]
    )


@router.get("/voices/library", response_model=VoiceLibraryResponse, tags=["voices"])
async def get_voice_library(
    category_id: str = Query(..., description="Category ID from /api/voices/categories"),
    gender: str | None = Query(None, description="Filter by gender: male | female"),
    page_size: int = Query(24, ge=1, le=50),
) -> VoiceLibraryResponse:
    """
    Return celebrity voices for a given profession category.
    Falls back to curated list when API key lacks voices_read permission.
    """
    cat = CATEGORY_MAP.get(category_id)
    if not cat:
        raise HTTPException(status_code=400, detail=f"Unknown category: {category_id}")

    cache_key = f"{category_id}:{gender}"
    cached = _cache.get(cache_key)
    if cached and (time.time() - cached[0]) < CACHE_TTL:
        voices = cached[1]
        logger.info(f"Voice library cache hit: {cache_key} ({len(voices)} voices)")
        return VoiceLibraryResponse(
            category=CategoryInfo(id=cat["id"], label=cat["label"], emoji=cat["emoji"], description=cat["description"]),
            voices=[VoiceItem(**v) for v in voices],
            total=len(voices),
        )

    settings = get_settings()
    api_key = settings.elevenlabs_api_key
    if not api_key:
        raise HTTPException(status_code=503, detail="ElevenLabs API key not configured")

    params: dict[str, Any] = {"page_size": page_size}
    if cat["el_category"]:
        params["category"] = cat["el_category"]
    if cat["el_search"]:
        params["search"] = cat["el_search"]
    if gender:
        params["gender"] = gender

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://api.elevenlabs.io/v1/shared-voices",
                headers={"xi-api-key": api_key},
                params=params,
            )
    except httpx.TimeoutException:
        return _curated_response(cat, category_id, "ElevenLabs timed out — showing curated selection.")
    except httpx.RequestError:
        return _curated_response(cat, category_id, "Network error — showing curated selection.")

    if resp.status_code in (401, 403):
        logger.info(f"voices_read permission missing — returning curated fallback for '{category_id}'")
        return _curated_response(
            cat,
            category_id,
            "Upgrade to ElevenLabs Creator plan to unlock actual celebrity voices. "
            "Preview selection shown — upgrade at elevenlabs.io to access the full library.",
        )

    if resp.status_code != 200:
        logger.warning(f"ElevenLabs shared-voices returned {resp.status_code}: {resp.text[:200]}")
        return _curated_response(cat, category_id, "Could not load live voices — showing curated selection.")

    body = resp.json()
    raw_voices = body.get("voices", [])
    voices_data = [
        {
            "voice_id": v.get("voice_id", ""),
            "name": v.get("name", ""),
            "gender": v.get("gender"),
            "accent": v.get("accent"),
            "age": v.get("age"),
            "description": v.get("description") or _build_description(v),
            "preview_url": v.get("preview_url"),
            "category": v.get("category"),
        }
        for v in raw_voices
        if v.get("voice_id")
    ]

    _cache[cache_key] = (time.time(), voices_data)
    logger.info(f"Fetched {len(voices_data)} live voices for category '{category_id}'")

    return VoiceLibraryResponse(
        category=CategoryInfo(id=cat["id"], label=cat["label"], emoji=cat["emoji"], description=cat["description"]),
        voices=[VoiceItem(**v) for v in voices_data],
        total=len(voices_data),
    )


def _curated_response(cat: dict, category_id: str, note: str) -> VoiceLibraryResponse:
    voices = CURATED_VOICES.get(category_id, [])
    return VoiceLibraryResponse(
        category=CategoryInfo(id=cat["id"], label=cat["label"], emoji=cat["emoji"], description=cat["description"]),
        voices=[VoiceItem(**v) for v in voices],
        total=len(voices),
        note=note,
        is_curated=True,
    )


def _build_description(v: dict) -> str:
    parts = []
    if v.get("accent"):
        parts.append(v["accent"])
    if v.get("age"):
        parts.append(v["age"])
    if v.get("gender"):
        parts.append(v["gender"])
    descriptors = v.get("descriptors", [])
    if descriptors:
        parts.extend(descriptors[:2])
    return ", ".join(parts) if parts else ""
