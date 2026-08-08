import os, json, glob, random, requests, shutil, sys
from dotenv import load_dotenv
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    pass
PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"
def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return []
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
    published.append({"video_name": video_name, "metadata": metadata})
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)
def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))
    if specific_video:
        if os.path.exists(specific_video): return specific_video, os.path.basename(specific_video)
        else: return None, None
    unpublished = [(v, os.path.basename(v)) for v in all_videos if os.path.basename(v) not in published]
    if unpublished: return unpublished[0]
    if all_videos:
        rc = get_repost_counts()
        weights = [max(1, 1000 // (3 ** min(rc.get(os.path.basename(v), 0), 6))) for v in all_videos]
        sel = random.choices(all_videos, weights=weights, k=1)[0]
        return sel, os.path.basename(sel)
    return None, None
def generate_caption():
    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")
    fallback_titles = [
        "This Bridge Was Built in Just 48 Hours - The Time-Lapse Is Insane",
        "Watch This Massive Bridge Go From Nothing to Stunning",
        "Engineering Marvel: Bridge Construction Time-Lapse",
        "From Foundation to Finish - This Bridge Build Is Pure Satisfaction",
        "How a 2-Kilometer Bridge Gets Built: Start to Finish",
        "This Bridge Construction Is So Satisfying You Won't Stop",
        "Bridge Builders Are Real-Life Superheroes",
        "The Most Incredible Bridge Construction You'll Ever See",
        "From Steel Beams to Sky-High Bridge",
        "This Bridge Took 3 Years to Build - In 1 Minute"
    ]
    fallback_descriptions = [
        "There's something mesmerizing about watching a bridge come together from nothing. From the first steel beam to the final cable tensioned into place, every step is a testament to human engineering. This time-lapse captures the entire journey - foundation work, towering pylons, careful placement of each segment, and that breathtaking moment when both sides meet.",
        "Every bridge tells a story of human ambition. From massive foundations deep underwater to precision placement of segments high above the river, the process is both terrifying and beautiful. Engineers perform a delicate dance with physics, weather, and gravity. When you see the final product spanning an impossible gap, you realize infrastructure isn't just functional - it's inspiring.",
        "Bridge construction is one of the most satisfying things to watch. There's something about seeing massive steel structures rise from nothing that captures your imagination. The precision required is extraordinary: each bolt, each weld, each cable has to be perfect. That's what makes bridge engineering so incredible."
    ]
    if not api_key:
        return random.choice(fallback_titles), random.choice(fallback_descriptions)
    vibes = [
        "awe-inspiring and celebratory - highlight the incredible engineering feat",
        "satisfying and mesmerizing - focus on the visual appeal of construction",
        "educational and fascinating - explain the engineering marvels",
        "dramatic and epic - make it feel like watching a movie"
    ]
    chosen_vibe = random.choice(vibes)
    prompt = (
        f"Write a unique, long, captivating title and description for a short video "
        f"for Facebook page 'Bridges Bountsy'. "
        f"Page posts bridge construction time-lapse videos. Content: steel beams, concrete foundations, cranes, engineering marvels. "
        f"Speak as a bridge engineering enthusiast. Vibe: {chosen_vibe}. "
        f"Description 4-6 sentences, engaging. Include: Like if you love bridge construction! Comment which bridge you want to see! Share with an engineering fan! Follow Bridges Bountsy! "
        f"Hashtags: #bridge #engineering #construction #timelapse #infrastructure #architecture #civilengineering #steel #megaproject #satisfying. "
        f'Return JSON: {{"title": "...", "description": "..."}}'
    )
    try:
        resp = requests.post("https://gen.pollinations.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.9, "seed": random.randint(1, 999999)},
            timeout=30)
        resp.raise_for_status()
        content = resp.json().get('choices', [{}])[0].get('message', {}).get('content', '')
        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)
        return result.get("title", random.choice(fallback_titles)), result.get("description", random.choice(fallback_descriptions))
    except: return random.choice(fallback_titles), random.choice(fallback_descriptions)
def main():
    print("=" * 60)
    print("DAILY AUTOMATION STARTING")
    print("=" * 60)
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("No new videos found. Exiting.")
        return
    print(f"Selected: {video_name}")
    title, description = generate_caption()
    print(f"Title: {title}")
    combined = f"{title}\n\n{description}"
    sf = {"instagram_reel": False, "instagram_story": False, "facebook_reel": False, "facebook_story": False, "threads": False, "youtube": False}
    try:
        r = upload_to_instagram(video_path, combined, is_story=False)
        if r and r.get('status') != 'skipped': sf["instagram_reel"] = True
    except: pass
    try:
        r = upload_to_instagram(video_path, combined, is_story=True)
        if r and r.get('status') != 'skipped': sf["instagram_story"] = True
    except: pass
    try:
        r = upload_to_facebook(video_path, description, title=title)
        if r and r.get('status') != 'skipped': sf["facebook_reel"] = True
    except: pass
    try:
        r = upload_to_facebook_story(video_path)
        if r and r.get('status') != 'skipped': sf["facebook_story"] = True
    except: pass
    try:
        r = upload_to_threads(video_path, combined)
        if r and r.get('status') != 'skipped': sf["threads"] = True
    except: pass
    try:
        upload_to_youtube(video_path, title, description, tags=["bridge","engineering","construction","timelapse","infrastructure","architecture","civilengineering","steel","megaproject","satisfying"])
        sf["youtube"] = True
    except: pass
    pl = get_already_published()
    recycled = any(i["video_name"] == video_name for i in pl)
    mark_as_published(video_name, {"title": title, "description": description, "success_flags": sf, "recycled": recycled})
    pd = "Published_Videos"
    if not os.path.exists(pd): os.makedirs(pd)
    try: shutil.move(video_path, os.path.join(pd, video_name))
    except: pass
    print("DAILY AUTOMATION COMPLETE")
if __name__ == "__main__":
    main()

