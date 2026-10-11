"""Portrait (1080x1920) animated-presenter video: 7 life tips, ~3 minutes.

Voice: Kokoro TTS. Character: drawn with Pillow, mouth driven by the audio envelope.
Usage: python3 make_tips_video.py <models_dir>
Outputs go to ./output_tips/
"""
import math
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
OUT = Path(__file__).parent / "output_tips"
TMP = OUT / "tmp"
TMP.mkdir(parents=True, exist_ok=True)
MODELS = Path(sys.argv[1])
FONT = "/usr/share/fonts/opentype/inter/Inter-{}.otf"
TARGET_SECONDS = 174.0  # YouTube Shorts allows up to 3:00

# (kicker, title, [sentences])
SCENES = [
    ("", "7 life tips in 3 minutes", [
        "Here are seven life tips that took me years to learn.",
        "You can steal them in under three minutes.",
        "Let's go."]),
    ("TIP 1", "The two-minute rule", [
        "Tip one. The two minute rule.",
        "If a task takes less than two minutes, do it right now.",
        "Reply to that message. Put the cup in the dishwasher.",
        "Small things pile up into a heavy mental load, and clearing them instantly builds momentum for the big stuff.",
        "Try it for one day, and see how much shorter your to do list feels."]),
    ("TIP 2", "Protect your sleep", [
        "Tip two. Protect your sleep.",
        "Try waking up at the same time every day, even on weekends.",
        "A steady schedule often does more for your energy than another coffee.",
        "And charge your phone across the room, so it is not the last thing you see at night.",
        "Your body loves a rhythm, and so does your focus."]),
    ("TIP 3", "Pay yourself first", [
        "Tip three. Pay yourself first.",
        "The moment your paycheck lands, move a fixed amount into savings automatically.",
        "Even a small amount counts.",
        "If you wait to save whatever is left at the end of the month, there usually is nothing left.",
        "Start with five percent if you can, and raise it every time you get a raise."]),
    ("TIP 4", "Write it down", [
        "Tip four. Write it down.",
        "Your brain is great at having ideas, and terrible at storing them.",
        "Keep one note on your phone for tasks, ideas, and things to remember.",
        "Once it is written down, your mind can stop looping on it, and that quiet feels amazing.",
        "Do a quick review each Sunday, and move what matters into your week."]),
    ("TIP 5", "Ask better questions", [
        "Tip five. Ask better questions.",
        "Instead of, how was your day, try, what was the best part of your day?",
        "People open up when a question is specific and curious.",
        "Then actually listen, without planning your reply. That is how real friendships get built.",
        "Try it at dinner tonight, and notice how the conversation changes."]),
    ("TIP 6", "Decide small things fast", [
        "Tip six. Decide small things fast.",
        "Most decisions can be undone, so do not spend an hour choosing a restaurant.",
        "Save your thinking for the choices that are big and hard to reverse, like your career, your health, and who you spend your time with.",
        "A good rule is, if it will not matter in a year, give it a minute, not an hour."]),
    ("TIP 7", "Take a ten-minute walk", [
        "Tip seven. Take a ten minute walk.",
        "When you feel stuck, stressed, or foggy, go outside and walk, with no phone if you can.",
        "Moving your body and changing your view is one of the cheapest ways to reset your mind.",
        "Even five minutes counts, so do not wait for the perfect time."]),
    ("", "Pick one. Start today.", [
        "That is all seven. You do not need to do them all.",
        "Pick one, and do it for a week.",
        "Small habits, repeated, change a life far more than big plans you never start.",
        "Follow for more, and tell me in the comments which tip you will try first."]),
]

PALETTES = [  # (top, bottom) per scene
    ((30, 41, 90), (88, 28, 135)), ((8, 80, 120), (6, 148, 162)), ((49, 46, 129), (30, 64, 175)),
    ((6, 95, 70), (21, 128, 61)), ((124, 45, 18), (194, 65, 12)), ((131, 24, 67), (190, 18, 60)),
    ((55, 48, 163), (109, 40, 217)), ((15, 118, 110), (14, 116, 144)), ((30, 41, 90), (88, 28, 135)),
]
SKIN, SKIN_SH, HAIR, SHIRT = (241, 194, 160), (222, 168, 134), (52, 36, 32), (250, 250, 250)
YELLOW = (255, 214, 10)


def font(name, size):
    return ImageFont.truetype(FONT.format(name), size)


# ---------- audio ----------
def synth(speed):
    kokoro = Kokoro(str(MODELS / "kokoro.onnx"), str(MODELS / "voices.bin"))
    sr = 24000
    chunks, timeline, t = [], [], 0.0  # timeline: (scene, sentence, start, end)
    for si, (_, _, sents) in enumerate(SCENES):
        for sent in sents:
            a, sr = kokoro.create(sent, voice="af_heart", speed=speed, lang="en-us")
            a = np.trim_zeros(np.round(a, 3), "b")  # drop trailing silence
            gap = np.zeros(int(sr * (0.45 if sent is sents[-1] else 0.22)), dtype=a.dtype)
            d = len(a) / sr
            timeline.append((si, sent, t, t + d))
            chunks += [a, gap]
            t += d + len(gap) / sr
    return np.concatenate(chunks), sr, timeline


# ---------- character ----------
HEAD_W, HEAD_H, PIVOT = 640, 760, (320, 560)
HEAD_POS = (220, 480)


def base_head():
    s = 2
    im = Image.new("RGBA", (HEAD_W * s, HEAD_H * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    e = lambda b, **k: d.ellipse([v * s for v in b], **k)
    d.rounded_rectangle([v * s for v in (80, 70, 560, 650)], radius=200 * s, fill=HAIR)  # hair back
    d.rectangle([v * s for v in (270, 470, 370, 620)], fill=SKIN_SH)  # neck
    e((100, 300, 140, 400), fill=SKIN_SH), e((500, 300, 540, 400), fill=SKIN_SH)  # ears
    e((105, 85, 535, 575), fill=SKIN)  # face
    # fringe
    pts = []
    for i in range(0, 61):
        a = math.pi + math.pi * i / 60
        pts.append((320 + 232 * math.cos(a), 300 + 250 * math.sin(a)))
    pts += [(500, 250), (440, 215), (350, 170), (270, 195), (190, 235), (130, 270)]
    d.polygon([(x * s, y * s) for x, y in pts], fill=HAIR)
    e((150, 395, 215, 445), fill=(255, 150, 150, 70)), e((425, 395, 490, 445), fill=(255, 150, 150, 70))  # cheeks
    d.arc([v * s for v in (295, 385, 345, 425)], 20, 160, fill=SKIN_SH, width=5 * s)  # nose
    return im.resize((HEAD_W, HEAD_H), Image.LANCZOS)


HEAD = base_head()


def face_patch(mouth, blink, brow):
    """Eyes, brows, mouth at 3x on a 400x280 patch located at (120,250) in head coords."""
    s = 3
    im = Image.new("RGBA", (400 * s, 280 * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ox, oy = 120, 250
    X = lambda x: (x - ox) * s
    Y = lambda y: (y - oy) * s
    for cx in (235, 405):
        by = 296 - brow * 12
        d.line([(X(cx - 38), Y(by + 3)), (X(cx), Y(by - 4)), (X(cx + 38), Y(by + 3))], fill=HAIR, width=11 * s, joint="curve")
        eh = max(3, 27 * (1 - blink))
        d.ellipse([X(cx - 21), Y(342 - eh), X(cx + 21), Y(342 + eh)], fill=(40, 28, 28))
        if blink < 0.5:
            d.ellipse([X(cx - 9), Y(334 - eh * 0.5), X(cx + 3), Y(346 - eh * 0.5)], fill=(255, 255, 255))
    cx, cy = 320, 462
    if mouth < 0.08:
        d.arc([X(cx - 42), Y(cy - 30), X(cx + 42), Y(cy + 22)], 15, 165, fill=(150, 60, 70), width=8 * s)
    else:
        w, h = 36 + 22 * mouth, 8 + 62 * mouth
        d.ellipse([X(cx - w), Y(cy - h * 0.35), X(cx + w), Y(cy + h)], fill=(110, 28, 44))
        if mouth > 0.3:
            d.rounded_rectangle([X(cx - w * 0.72), Y(cy - h * 0.3), X(cx + w * 0.72), Y(cy + h * 0.12)], radius=6 * s, fill=(255, 255, 255))
            d.ellipse([X(cx - w * 0.5), Y(cy + h * 0.45), X(cx + w * 0.5), Y(cy + h * 0.95)], fill=(232, 110, 120))
    return im.resize((400, 280), Image.LANCZOS)


def head_frame(mouth, blink, brow, angle):
    h = HEAD.copy()
    h.alpha_composite(face_patch(mouth, blink, brow), (120, 250))
    return h.rotate(angle, resample=Image.BICUBIC, center=PIVOT)


# ---------- scene backgrounds ----------
def make_bg(si):
    top, bot = PALETTES[si]
    t = np.linspace(0, 1, H)[:, None, None]
    arr = (np.array(top)[None, None, :] * (1 - t) + np.array(bot)[None, None, :] * t)
    arr = np.repeat(arr, W, axis=1).astype(np.uint8)
    im = Image.fromarray(arr, "RGB")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.ellipse([-250, 1250, 450, 1950], fill=(255, 255, 255, 18))
    d.ellipse([700, 80, 1300, 680], fill=(255, 255, 255, 14))
    # presenter badge: circle with torso clipped inside
    cx, cy, r = 540, 1020, 400
    d.ellipse([cx - r - 14, cy - r - 14, cx + r + 14, cy + r + 14], fill=(255, 255, 255, 40))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 235))
    torso = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(torso)
    td.rounded_rectangle([140, 1110, 940, 1700], radius=230, fill=(40, 52, 110))
    td.polygon([(470, 1090), (610, 1090), (540, 1250)], fill=SKIN_SH)
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    torso.putalpha(Image.composite(torso.getchannel("A"), Image.new("L", (W, H), 0), mask))
    ov.alpha_composite(torso)
    im = im.convert("RGBA")
    im.alpha_composite(ov)
    return im.convert("RGB")


def make_title(si):
    kicker, title, _ = SCENES[si]
    im = Image.new("RGBA", (W, 420), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = 0
    if kicker:
        kf = font("ExtraBold", 64)
        d.text((W // 2, y), kicker, font=kf, fill=YELLOW, anchor="mt")
        y += 100
    tf = font("ExtraBold", 92 if kicker else 104)
    words, lines, cur = title.split(), [], ""
    for w in words:
        if tf.getlength((cur + " " + w).strip()) > W - 160 and cur:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    lines.append(cur)
    for ln in lines:
        d.text((W // 2, y), ln, font=tf, fill=(255, 255, 255), anchor="mt", stroke_width=3, stroke_fill=(0, 0, 0, 70))
        y += 112
    return im


# ---------- captions ----------
CAP_FONT = font("ExtraBold", 80)


def make_caption(words, active):
    im = Image.new("RGBA", (W, 330), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lines, cur, cw = [], [], 0
    sp = CAP_FONT.getlength(" ")
    for i, w in enumerate(words):
        wl = CAP_FONT.getlength(w)
        if cur and cw + sp + wl > W - 140:
            lines.append(cur)
            cur, cw = [], 0
        cur.append((i, w, wl))
        cw += (sp if len(cur) > 1 else 0) + wl
    lines.append(cur)
    y = 0
    for ln in lines:
        total = sum(w[2] for w in ln) + sp * (len(ln) - 1)
        x = (W - total) / 2
        for i, w, wl in ln:
            d.text((x, y), w, font=CAP_FONT, fill=YELLOW if i == active else (255, 255, 255),
                   stroke_width=9, stroke_fill=(15, 15, 30))
            x += wl + sp
        y += 100
    return im


def build_words(timeline):
    """-> list of caption chunks: (words, [(start, end)...], scene). Chunks of <= 5 words."""
    chunks = []
    for si, sent, a, b in timeline:
        ws = sent.split()
        weights = [len(w) + 2 for w in ws]
        tot, t, spans = sum(weights), a, []
        for wt in weights:
            dt = (b - a) * wt / tot
            spans.append((t, t + dt))
            t += dt
        i = 0
        while i < len(ws):
            n = min(5, len(ws) - i)
            if len(ws) - i - n == 1:
                n = len(ws) - i if len(ws) - i <= 6 else n - 1
            chunks.append((ws[i:i + n], spans[i:i + n], si))
            i += n
    return chunks


# ---------- rendering ----------
G = {}


def render_range(args):
    k, a, b = args
    seg = TMP / f"seg_{k}.mp4"
    p = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-g", "30",
         "-pix_fmt", "yuv420p", str(seg)], stdin=subprocess.PIPE)
    cap_cache = {}
    for f in range(a, b):
        t = f / FPS
        si = G["scene_at"](t)
        frame = G["bg"][si].copy()
        # title (fade + slide in)
        ts = t - G["scene_start"][si]
        k_in = min(1.0, ts / 0.35)
        title = G["title"][si]
        if k_in < 1:
            title = title.copy()
            title.putalpha(title.getchannel("A").point(lambda v: int(v * k_in)))
        frame.paste(title, (0, int(110 + 30 * (1 - k_in))), title)
        # head
        m = float(G["mouth"][min(f, len(G["mouth"]) - 1)])
        phase = t % 3.7
        blink = max(0.0, 1 - abs(phase - 3.4) / 0.1) if 3.3 < phase < 3.5 else 0.0
        brow = 0.5 * m + 0.5 * math.sin(t * 1.3) ** 2
        angle = 1.8 * math.sin(2 * math.pi * t / 4.1)
        dy = 7 * math.sin(2 * math.pi * t / 3.2) + 5 * m
        head = head_frame(m, blink, brow, angle)
        frame.paste(head, (HEAD_POS[0], int(HEAD_POS[1] + dy)), head)
        # caption
        ci, wi = G["caption_at"](t)
        if ci is not None:
            key = (ci, wi)
            if key not in cap_cache:
                cap_cache[key] = make_caption(G["chunks"][ci][0], wi)
            cap = cap_cache[key]
            frame.paste(cap, (0, 1480), cap)
        # progress bar
        d = ImageDraw.Draw(frame)
        d.rectangle([0, 0, int(W * t / G["total"]), 12], fill=YELLOW)
        p.stdin.write(frame.tobytes())
    p.stdin.close()
    p.wait()
    return seg


def main():
    speed = 0.92
    for _ in range(3):
        audio, sr, timeline = synth(speed)
        total = len(audio) / sr + 0.6
        print(f"speed {speed:.2f} -> {total:.1f}s", flush=True)
        if abs(total - TARGET_SECONDS) < 3:
            break
        speed = round(speed * total / TARGET_SECONDS, 3)
    audio = np.concatenate([audio, np.zeros(int(sr * 0.6), dtype=audio.dtype)])
    sf.write(TMP / "voice.wav", audio, sr)
    nframes = int(total * FPS)

    # mouth envelope
    win = int(sr * 0.045)
    env = np.array([np.sqrt(np.mean(audio[max(0, int(i / FPS * sr) - win):int(i / FPS * sr) + win] ** 2) + 1e-12)
                    for i in range(nframes)])
    env = np.clip(env / (np.percentile(env, 95) + 1e-9), 0, 1) ** 0.8
    mouth, prev = [], 0.0
    for v in env:
        prev = v if v > prev else prev * 0.55 + v * 0.45
        mouth.append(prev if prev > 0.06 else 0.0)

    chunks = build_words(timeline)
    scene_start = {si: min(a for s, _, a, _ in timeline if s == si) for si in range(len(SCENES))}
    scene_start[0] = 0.0
    starts = sorted(scene_start.items(), key=lambda kv: kv[1])

    def scene_at(t):
        cur = 0
        for si, st in starts:
            if t >= st - 0.05:
                cur = si
        return cur

    def caption_at(t):
        for ci, (ws, spans, _) in enumerate(chunks):
            if spans[0][0] - 0.05 <= t <= spans[-1][1] + 0.12:
                wi = 0
                for i, (a, b) in enumerate(spans):
                    if t >= a:
                        wi = i
                return ci, wi
        return None, None

    G.update(bg=[make_bg(i) for i in range(len(SCENES))], title=[make_title(i) for i in range(len(SCENES))],
             mouth=mouth, scene_start=scene_start, scene_at=scene_at, caption_at=caption_at,
             chunks=chunks, total=total)

    n = 4
    step = math.ceil(nframes / n / FPS) * FPS
    jobs = [(k, k * step, min(nframes, (k + 1) * step)) for k in range(n) if k * step < nframes]
    with Pool(len(jobs)) as pool:
        segs = pool.map(render_range, jobs)
    lst = TMP / "list.txt"
    lst.write_text("".join(f"file '{s.resolve()}'\n" for s in segs))
    joined = TMP / "video_only.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(joined)], check=True)
    final = OUT / "7-life-tips-in-3-minutes.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(joined), "-i", str(TMP / "voice.wav"),
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-shortest", str(final)], check=True)

    # captions file
    def stamp(x):
        ms = int(round(x * 1000))
        return f"{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}"
    srt = [f"{i+1}\n{stamp(a)} --> {stamp(b)}\n{s}\n" for i, (_, s, a, b) in enumerate(timeline)]
    (OUT / "captions.srt").write_text("\n".join(srt))
    print("done", final, f"{total:.1f}s", flush=True)


if __name__ == "__main__":
    main()
