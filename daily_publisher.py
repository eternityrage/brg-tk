import os
import sys
import json
import glob
import random
import re
import urllib.parse
import shutil
import datetime
from pathlib import Path
import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"
YOUTUBE_STATE_FILE = "youtube_publish_state.json"

# Allowed weekdays for YouTube: Monday (0), Wednesday (2), Friday (4), Sunday (6)
ALLOWED_YOUTUBE_WEEKDAYS = {0, 2, 4, 6}
WEEKDAY_NAMES = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday"
}


# ==============================================================================
# BRIDGES BOUNTSY KNOWLEDGE BASE & CREATIVE HOOKS
# ==============================================================================

BRIDGES_BOUNTSY_DATABASE = {
    "cable_stayed_suspension": {
        "category": "Cable-Stayed & Suspension Bridge",
        "emoji": "🌉✨",
        "focus": "towering concrete pylons, high-tension stay cables, and aerial cable spinning over wide river gaps",
        "titles": [
            "Towering Spans: Inside This Insane Cable-Stayed Bridge Build! 🌉✨",
            "Watch Massive Cable Towers Rise Above the Clouds! 🏗️🌉",
            "How Engineers Spanned an Impossible Gap: Suspension Bridge Time-Lapse 🌉🔥",
            "The Ultimate Cable-Stayed Bridge Engineering Marvel! 🌉📐",
            "From Sea Bed to Sky: Incredible Bridge Build Time-Lapse 🏗️🌊",
            "Engineering Grandeur: Towering Pylons & High-Tension Cables 🌉⚡"
        ],
        "descriptions": [
            "Witness the breathtaking precision of cable-stayed bridge engineering! From deep underwater caissons to towering concrete pylons and high-tension stay cables, every stage is a masterclass in modern civil engineering.\n\n🌉 Which bridge marvel is your all-time favorite? Drop a comment below!\n👉 Follow Bridges Bountsy for daily epic bridge construction and megaprojects! 🏗️✨\n\n#BridgesBountsy #Bridge #Engineering #Construction #TimeLapse #CivilEngineering #Infrastructure #Architecture #MegaProject #Shorts #Reels",
            "From the first foundation pour to the final stay cable tensioning, watch this impossible crossing come to life. The balance of physics, tension, and structural elegance is pure art.\n\n💬 Rate this bridge engineering feat from 1 to 10 in the comments!\n👉 Follow @BridgesBountsy for the most satisfying bridge builds! 🌉🔥\n\n#BridgesBountsy #Bridge #SuspensionBridge #EngineeringMarvel #CivilEngineering #Construction #TimeLapse #Shorts #Reels"
        ]
    },
    "steel_arch_truss": {
        "category": "Steel Arch & Truss Bridge",
        "emoji": "🏗️🔥",
        "focus": "heavy structural steel beams, massive arch spans, and precision bolt and weld assembly",
        "titles": [
            "Heavy Steel in the Sky: Massive Bridge Arch Time-Lapse! 🏗️🔥",
            "How Thousands of Tons of Steel Become a Masterpiece 🌉💪",
            "Watch This Monster Steel Truss Bridge Get Built! 🏗️🌉",
            "The Moment Two Giant Bridge Arches Meet in the Middle! 🌉✨",
            "Steel Giants: Incredible Arch Bridge Construction Time-Lapse 🏗️⚡"
        ],
        "descriptions": [
            "Thousands of tons of fabricated structural steel lifted hundreds of meters in the air. Watch this incredible time-lapse showing how engineers piece together this monumental steel arch bridge with millimeter precision.\n\n🏗️ Tag an engineer or construction fan who needs to see this!\n👉 Follow Bridges Bountsy for more mind-blowing infrastructure megaprojects! 🌉🔥\n\n#BridgesBountsy #Bridge #SteelBridge #Engineering #Construction #TimeLapse #CivilEngineering #Infrastructure #MegaProject #Shorts #Reels",
            "Watching these massive curved steel trusses lock together over the gorge is pure engineering magic. Incredible heavy machinery and fearless crews building our modern world.\n\n💬 Drop a 🔥 if you love structural steel engineering!\n👉 Follow Bridges Bountsy for daily bridge construction! 🌉✨\n\n#BridgesBountsy #Bridge #CivilEngineering #Architecture #SteelTruss #Construction #TimeLapse #Shorts #Reels"
        ]
    },
    "precast_segmental": {
        "category": "Precast Segmental Box Girder Bridge",
        "emoji": "🏗️🌉",
        "focus": "launching gantries, precast concrete box girders, and segment-by-segment installation",
        "titles": [
            "This Giant Launching Gantry Builds a Bridge in Mid-Air! 🏗️🌉",
            "Watch 100-Ton Concrete Segments Form a Mega Bridge! 🌉✨",
            "Satisfying Precast Segment Bridge Construction Time-Lapse! 🏗️😍",
            "Next-Level Bridge Engineering: Segment by Segment! 🌉⚡",
            "The Ultimate Highway Viaduct Build: Giant Gantry in Action 🏗️🚗"
        ],
        "descriptions": [
            "Notice the immense launching gantry machine moving smoothly across the piers, lifting and gluing precast concrete box girders into place. This is rapid bridge construction at its absolute finest.\n\n💬 How satisfying is this construction speed on a scale of 1-10?\n👉 Follow Bridges Bountsy for daily bridge construction time-lapses! 🌉🏗️\n\n#BridgesBountsy #Bridge #CivilEngineering #Construction #TimeLapse #Engineering #MegaProject #Architecture #Shorts #Reels",
            "Like giant puzzle pieces in the sky! Watch how balanced cantilever construction allows massive viaducts to stretch across the landscape with zero falsework beneath.\n\n🏗️ Share this with someone who loves watching heavy construction machinery!\n👉 Follow Bridges Bountsy for more! 🌉✨\n\n#BridgesBountsy #Bridge #ConcreteBridge #CivilEngineering #ConstructionLife #TimeLapse #Shorts #Reels"
        ]
    },
    "sea_crossing_megaproject": {
        "category": "Sea-Crossing Megaproject",
        "emoji": "🌊🌉",
        "focus": "open-ocean bridge engineering, offshore deepwater caissons, and record-breaking spans",
        "titles": [
            "Building an Impossible Sea Bridge Across the Open Ocean! 🌊🌉",
            "World Record Megaproject: Ocean Bridge Time-Lapse! 🏗️🌊",
            "Deep Water Engineering: How They Built This Massive Sea Bridge 🌊🌉",
            "Engineering Marvel: Spanning Miles of Open Water! 🌉🔥",
            "Conquering Ocean Currents: The Ultimate Marine Bridge Build 🌊🏗️"
        ],
        "descriptions": [
            "Battling fierce ocean currents, typhoons, and deep seafloor mud, engineers conquered nature to build this world-class sea-crossing bridge. A monumental human achievement in civil engineering.\n\n🌊 Would you drive across this bridge in a storm? Let us know below!\n👉 Follow Bridges Bountsy for the world's greatest bridges and megaprojects! 🌉✨\n\n#BridgesBountsy #MegaProject #Bridge #OceanBridge #CivilEngineering #Construction #Engineering #Infrastructure #Shorts #Reels",
            "From marine pile driving barges to artificial island junctions: witness how human ambition bridges the deepest waters on earth.\n\n💬 What is the most impressive ocean bridge you have ever crossed?\n👉 Follow Bridges Bountsy for world-class bridge documentaries and time-lapses! 🌊🌉\n\n#BridgesBountsy #SeaBridge #Engineering #CivilEngineering #MegaStructure #Shorts #Reels"
        ]
    },
    "satisfying_timelapse": {
        "category": "Satisfying Bridge Time-Lapse",
        "emoji": "🌉😍",
        "focus": "fast-paced time-lapse, rapid progress from foundation to finished roadway, pure visual satisfaction",
        "titles": [
            "From Muddy River to Mega Bridge in 60 Seconds! 🏗️🌉",
            "The Most Satisfying Bridge Construction Time-Lapse Ever! 🌉😍",
            "Watch 3 Years of Bridge Construction in 1 Minute! 🏗️✨",
            "Pure Engineering Satisfaction: Bridge Build Time-Lapse 🌉🔥",
            "How This Incredible Bridge Was Built: Start to Finish 🏗️🌉"
        ],
        "descriptions": [
            "There's something deeply satisfying about watching a bridge rise from raw foundations to an open highway in under a minute. Human ingenuity and heavy machinery working in total harmony.\n\n🌉 Drop a 🔥 if you love engineering time-lapses!\n👉 Follow Bridges Bountsy for daily bridge builds and civil engineering! 🏗️⚡\n\n#BridgesBountsy #Bridge #Satisfying #TimeLapse #Engineering #Construction #CivilEngineering #Architecture #Shorts #Reels",
            "Months of relentless planning, millions of worker hours, and thousands of tons of concrete and steel compressed into pure visual satisfaction.\n\n💬 Tag a friend who loves satisfying time-lapses!\n👉 Follow @BridgesBountsy for your daily dose of infrastructure wonder! 🌉✨\n\n#BridgesBountsy #TimeLapse #SatisfyingVideos #CivilEngineering #Bridge #Engineering #Shorts #Reels"
        ]
    }
}


# ==============================================================================
# STATE & LOGGING MANAGEMENT
# ==============================================================================

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        try:
            with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    return []


def get_repost_counts():
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts


def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "published_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)


def select_video(specific_video=None):
    if specific_video and os.path.exists(specific_video):
        return specific_video, os.path.basename(specific_video)

    published = [item.get("video_name") for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")) + glob.glob("*.mp4"))

    # Prefer unpublished videos
    unpublished = [(v, os.path.basename(v)) for v in all_videos if os.path.basename(v) not in published]
    if unpublished:
        return unpublished[0]

    # If all published, weighted random selection based on lowest repost count
    if all_videos:
        rc = get_repost_counts()
        weights = [max(1, 1000 // (3 ** min(rc.get(os.path.basename(v), 0), 6))) for v in all_videos]
        sel = random.choices(all_videos, weights=weights, k=1)[0]
        return sel, os.path.basename(sel)

    return None, None


# ==============================================================================
# CONTENT & CAPTION ENGINE
# ==============================================================================

def extract_video_subject(video_name: str) -> dict:
    """Identifies the bridge category from video filename."""
    clean_name = os.path.basename(video_name or "").lower()
    clean_name = re.sub(r'[_\-\.]', ' ', clean_name)

    if any(k in clean_name for k in ['cable', 'stay', 'suspension', 'tower', 'pylon']):
        return BRIDGES_BOUNTSY_DATABASE['cable_stayed_suspension']
    elif any(k in clean_name for k in ['steel', 'arch', 'truss', 'beam']):
        return BRIDGES_BOUNTSY_DATABASE['steel_arch_truss']
    elif any(k in clean_name for k in ['segment', 'gantry', 'box', 'girder', 'precast', 'viaduct']):
        return BRIDGES_BOUNTSY_DATABASE['precast_segmental']
    elif any(k in clean_name for k in ['sea', 'ocean', 'marine', 'island', 'megaproject', 'water']):
        return BRIDGES_BOUNTSY_DATABASE['sea_crossing_megaproject']

    return random.choice(list(BRIDGES_BOUNTSY_DATABASE.values()))


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'(?i)^(here is|sure,|certainly|note:|as requested).*?\n', '', text)
    text = re.sub(r'(Support\s+Pollinations|Powered\s+by\s+Pollinations|🌸\s*Ad\s*🌸).*$', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = text.replace('"', '').replace('“', '').replace('”', '').strip()
    return text


def generate_caption(video_name=None):
    """
    Generates a high-converting, matching title and description for Bridges Bountsy.
    Returns: (title, description)
    """
    subject = extract_video_subject(video_name or "")
    category = subject.get("category", "Bridge Construction")
    focus = subject.get("focus", "satisfying bridge construction and civil engineering time-lapse")
    emoji = subject.get("emoji", "🌉✨")

    fallback_titles = subject.get("titles") or [f"Watch This Massive Bridge Rise From Nothing! {emoji}"]
    fallback_descriptions = subject.get("descriptions") or [
        f"Witness the breathtaking engineering behind this {category.lower()}! From foundation caissons to towering spans, every step showcases the marvel of modern civil engineering.\n\n🌉 Would you drive across this bridge? Let us know below!\n👉 Follow Bridges Bountsy for daily bridge builds and megaprojects! 🏗️✨\n\n#BridgesBountsy #Bridge #Engineering #Construction #TimeLapse #CivilEngineering #Infrastructure #MegaProject #Shorts #Reels"
    ]

    api_key = os.getenv("POLLINATIONS_API_KEY", "").strip()
    model = os.getenv("AI_MODEL", "openai").strip()

    if not api_key:
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

    vibes = [
        "awe-inspiring, celebrate the incredible civil engineering feat",
        "deeply satisfying, focus on the visual harmony of time-lapse construction",
        "educational and captivating, explain the megaproject structural scale"
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a viral title and captivating description for 'Bridges Bountsy', "
        f"a social media page sharing satisfying bridge construction time-lapse videos and civil engineering megaprojects.\n"
        f"Theme: {category} {emoji}.\n"
        f"Focus: {focus}.\n"
        f"Tone: {chosen_vibe}.\n\n"
        f"CRITICAL REQUIREMENTS:\n"
        f"1. TITLE: Extremely catchy hook under 70 characters with emoji (e.g. 'Watch This Massive Bridge Rise From Nothing! 🌉✨').\n"
        f"2. DESCRIPTION: 3-4 engaging sentences celebrating human engineering ambition and machinery.\n"
        f"3. ENGAGEMENT: Include an interactive question and follow CTA: '👉 Follow Bridges Bountsy for daily epic bridge construction and megaprojects! 🏗️✨'.\n"
        f"4. HASHTAGS: #BridgesBountsy #Bridge #Engineering #Construction #TimeLapse #CivilEngineering #Infrastructure #Architecture #MegaProject #Shorts #Reels\n\n"
        f"OUTPUT FORMAT: Return raw JSON ONLY in this format:\n"
        f'{{"title": "...", "description": "..."}}'
    )

    try:
        url = "https://gen.pollinations.ai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.85,
            "seed": random.randint(1, 999999)
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=25)
        if resp.status_code == 200:
            content = resp.json().get('choices', [{}])[0].get('message', {}).get('content', '')
            content = clean_text(content)
            content = content.replace("```json", "").replace("```", "").strip()
            result = json.loads(content)
            title = result.get("title", "").strip()
            description = result.get("description", "").strip()

            if title and len(title) > 95:
                title = title[:92].rstrip() + "..."

            if description and "#BridgesBountsy" not in description:
                description = f"{description}\n\n👉 Follow Bridges Bountsy for daily bridge builds! 🌉🏗️\n#BridgesBountsy #Bridge #Engineering #CivilEngineering #TimeLapse #Shorts #Reels"

            if title and len(title) >= 10 and description and len(description) >= 40:
                return title, description
    except Exception as e:
        print(f"  [WARN] Pollinations caption generation fallback: {e}")

    return random.choice(fallback_titles), random.choice(fallback_descriptions)


def generate_pinned_comment(description, title=None):
    """Generates pinned comment for Facebook and YouTube."""
    custom_link = os.getenv("PINNED_COMMENT_LINK", "").strip()
    if custom_link:
        return f"🌉 Full Megaproject Docs & Engineering Blueprints: {custom_link}\n\n👉 Follow Bridges Bountsy for daily bridge construction time-lapses! 🏗️✨"
    return "🌉 Welcome to Bridges Bountsy! Which engineering marvel should we feature next? Drop it in the comments! 🏗️✨\n👉 Follow & subscribe for daily satisfying bridge builds and megaprojects! 🚀"


# ==============================================================================
# YOUTUBE STRICT SCHEDULING (MONDAY, WEDNESDAY, FRIDAY, SUNDAY - MAX ONCE A DAY)
# ==============================================================================

def get_last_youtube_publish_date():
    """
    Finds the last date (datetime.date) on which a video was published to YouTube.
    First checks youtube_publish_state.json, then published_videos.json.
    """
    # 1. State file check
    if os.path.exists(YOUTUBE_STATE_FILE):
        try:
            with open(YOUTUBE_STATE_FILE, 'r', encoding='utf-8') as f:
                state = json.load(f)
                d_str = state.get("last_published_date")
                if d_str:
                    return datetime.date.fromisoformat(d_str)
        except Exception as e:
            print(f"[youtube schedule] Notice reading {YOUTUBE_STATE_FILE}: {e}")

    # 2. published_videos.json check
    published = get_already_published()
    for entry in reversed(published):
        metadata = entry.get("metadata", {})
        success_flags = metadata.get("success_flags", {})
        yt_success = success_flags.get("youtube") is True or metadata.get("youtube_published") is True
        pub_at = entry.get("published_at") or metadata.get("youtube_published_at")
        if yt_success and pub_at:
            try:
                return datetime.date.fromisoformat(pub_at[:10])
            except Exception:
                pass

    return None


def should_publish_to_youtube():
    """
    Strict YouTube Publishing Schedule for Bridges Bountsy:
    1. Publishes ONLY on Monday, Wednesday, Friday, and Sunday (4 times a week).
    2. Publishes at most ONCE per day on those allowed days.
    """
    today = datetime.datetime.now(datetime.timezone.utc).date()
    weekday = today.weekday()
    weekday_name = WEEKDAY_NAMES[weekday]

    # Check 1: Day of week constraint
    if weekday not in ALLOWED_YOUTUBE_WEEKDAYS:
        days_ahead = 1
        while (weekday + days_ahead) % 7 not in ALLOWED_YOUTUBE_WEEKDAYS:
            days_ahead += 1
        next_date = today + datetime.timedelta(days=days_ahead)
        next_day_name = WEEKDAY_NAMES[next_date.weekday()]
        return False, (
            f"Today is {weekday_name} ({today}). "
            f"Policy: YouTube publishes ONLY on Monday, Wednesday, Friday, and Sunday. "
            f"Next scheduled YouTube publish is {next_day_name} ({next_date})."
        )

    # Check 2: Max once a day constraint
    last_date = get_last_youtube_publish_date()
    if last_date is not None:
        if last_date == today:
            return False, f"YouTube has ALREADY published today ({weekday_name}, {today}). Policy: Maximum once a day on allowed days."
        if last_date > today:
            return False, f"Clock anomaly: Last YouTube publish recorded in future ({last_date}). Skipping YouTube upload."

    return True, f"Today is {weekday_name} ({today}) - scheduled YouTube publishing day! Ready to upload."


def record_youtube_publish(video_name, video_id=None):
    """Records the successful YouTube publication state."""
    today = datetime.datetime.now(datetime.timezone.utc).date()
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    state = {
        "last_published_date": today.isoformat(),
        "last_published_at": now_iso,
        "last_video_name": video_name,
        "last_video_id": video_id or ""
    }
    try:
        with open(YOUTUBE_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=4)
        print(f"[youtube schedule] ✅ Recorded YouTube publish state for {today.isoformat()}")
    except Exception as e:
        print(f"[youtube schedule] ⚠️ Error saving {YOUTUBE_STATE_FILE}: {e}")


# ==============================================================================
# MULTI-PLATFORM PUBLISHING
# ==============================================================================

def publish(video_path, publish_to_facebook=True, publish_to_instagram=True, publish_to_youtube=True):
    video_name = os.path.basename(video_path)
    title, description = generate_caption(video_name)
    combined = f"{title}\n\n{description}"
    pinned_comment = generate_pinned_comment(description, title)

    print(f"\n[METADATA] Title: {title}")
    print(f"[METADATA] Description:\n{description}\n")

    sf = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }

    # 1. Instagram (Daily on every run)
    if publish_to_instagram:
        try:
            from upload.upload_instagram import upload_to_instagram
            r = upload_to_instagram(video_path, combined, is_story=False)
            if r and r.get('status') != 'skipped':
                sf["instagram_reel"] = True
        except Exception as e:
            print(f"[instagram] Error uploading reel: {e}")

        try:
            from upload.upload_instagram import upload_to_instagram
            r = upload_to_instagram(video_path, combined, is_story=True)
            if r and r.get('status') != 'skipped':
                sf["instagram_story"] = True
        except Exception as e:
            print(f"[instagram] Error uploading story: {e}")

    # 2. Facebook (Daily on every run)
    if publish_to_facebook:
        try:
            from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
            r = upload_to_facebook(video_path, description, title=title)
            if r and r.get('status') != 'skipped':
                sf["facebook_reel"] = True
        except Exception as e:
            print(f"[facebook] Error uploading reel: {e}")

        try:
            from upload.upload_facebook import upload_to_facebook_story
            r = upload_to_facebook_story(video_path)
            if r and r.get('status') != 'skipped':
                sf["facebook_story"] = True
        except Exception as e:
            print(f"[facebook] Error uploading story: {e}")

    # 3. Threads (Daily on every run if configured)
    try:
        from upload.upload_threads import upload_to_threads
        r = upload_to_threads(video_path, combined)
        if r and r.get('status') != 'skipped':
            sf["threads"] = True
    except Exception as e:
        pass

    # 4. YouTube Shorts (Strict Schedule: Mon, Wed, Fri, Sun - max once a day)
    yt_details = None
    if publish_to_youtube:
        print("\n" + "-" * 50)
        print("🎬 YOUTUBE SHORTS PUBLISHING EVALUATION (Bridges Bountsy)")
        print("-" * 50)

        should_post, reason = should_publish_to_youtube()
        print(f"[youtube schedule] Decision: {'✅ PROCEED' if should_post else '⏭️ SKIP'}")
        print(f"[youtube schedule] Reason: {reason}")

        if should_post:
            try:
                from upload.upload_to_youtube import upload_to_youtube
                yt_res = upload_to_youtube(
                    video_path=video_path,
                    title=title,
                    description=description,
                    category_id='28'  # 28 = Science & Technology
                )
                if yt_res.get('status') == 'success':
                    sf["youtube"] = True
                    yt_details = yt_res
                    record_youtube_publish(video_name, yt_res.get('id'))
                    print(f"[youtube] 🎉 YouTube upload succeeded! URL: {yt_res.get('url')}")
                else:
                    print(f"[youtube] ❌ YouTube upload failed: {yt_res.get('error')}")
            except Exception as e:
                print(f"[youtube] ❌ Exception during YouTube upload: {e}")
        else:
            yt_details = {"status": "skipped", "reason": reason}

    return {
        "title": title,
        "description": description,
        "success_flags": sf,
        "youtube_details": yt_details
    }


def main():
    print("=" * 60)
    print("🚀 BRIDGES BOUNTSY DAILY AUTOMATION STARTING")
    print("=" * 60)

    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)

    if not video_path:
        print("No new videos found. Exiting.")
        return

    print(f"Selected: {video_name}")
    results = publish(video_path)

    pl = get_already_published()
    recycled = any(i.get("video_name") == video_name for i in pl)

    metadata = {
        "title": results["title"],
        "description": results["description"],
        "success_flags": results["success_flags"],
        "recycled": recycled
    }
    if results["success_flags"].get("youtube"):
        metadata["youtube_published"] = True
        metadata["youtube_published_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    mark_as_published(video_name, metadata)

    pd = "Published_Videos"
    if not os.path.exists(pd):
        os.makedirs(pd)
    try:
        shutil.move(video_path, os.path.join(pd, video_name))
    except Exception:
        pass

    print("=" * 60)
    print("🎉 BRIDGES BOUNTSY AUTOMATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
