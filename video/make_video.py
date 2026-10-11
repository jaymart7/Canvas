"""Builds the YouTube video: slides (Pillow) + voiceover (Kokoro TTS) + ffmpeg.

Usage: python3 make_video.py <models_dir>   (models_dir has kokoro.onnx + voices.bin)
Outputs go to ./output/
"""
import subprocess
import sys
import textwrap
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
OUT = Path(__file__).parent / "output"
TMP = OUT / "tmp"
TMP.mkdir(parents=True, exist_ok=True)
MODELS = Path(sys.argv[1])

F = "/usr/share/fonts/opentype/inter/Inter-{}.otf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
BG, FG, MUTED = (15, 23, 42), (248, 250, 252), (148, 163, 184)
ACCENT, BOX = (56, 189, 248), (30, 41, 59)

TITLE = "5 Ways to Use AI at Work This Week"

# (kicker, headline, prompt-box text or None, narration)
SCENES = [
    ("", TITLE, None,
     "Most people use A.I. like a search engine. Type a question, get an answer, move on. "
     "But the people saving hours every week use it like a coworker. "
     "Here are five ways to do that, with the exact prompts, so you can try them today."),
    ("FIRST, ONE RULE", "AI drafts. You decide.",
     "• Never paste confidential or client data\n• Always check facts, numbers and names\n• Edit the result so it sounds like you",
     "One rule before we start. A.I. drafts, you decide. Never paste confidential or client information into a public tool. "
     "Always check facts, numbers and names. And edit the result so it sounds like you wrote it. Okay, let's go."),
    ("WAY 1", "Turn messy notes into a clear email",
     "Rewrite these notes as a short, friendly email.\nKeep it under 120 words. Put the ask in the\nfirst two lines.\n\nNotes: [paste your rough notes here]",
     "Number one. Turn messy notes into a clear email. Paste your rough thoughts, and ask for a short, friendly email "
     "with the request in the first two lines. Setting a word limit is the secret. It forces the draft to be tight."),
    ("WAY 2", "Pull action items out of long text",
     "Read this meeting transcript. List:\n1) decisions made  2) action items with owner\nand deadline  3) open questions.\nIf something is missing, write 'not stated'.",
     "Number two. Pull action items out of long text. Give it a meeting transcript and ask for decisions, action items with an owner "
     "and a deadline, and open questions. The line that matters is, if something is missing, write not stated. "
     "That stops the tool from guessing."),
    ("WAY 3", "Practice the hard conversation first",
     "Act as my manager. I want to ask for a raise.\nPush back realistically with 3 objections, one at\na time. After each answer, give me feedback.",
     "Number three. Practice the hard conversation first. Ask the A.I. to play your manager, push back with three realistic objections, "
     "one at a time, and give you feedback after each answer. It costs nothing to practice badly here, and that is the whole point."),
    ("WAY 4", "Turn a messy process into a checklist",
     "Here is how I do [task], in rough order.\nTurn it into a numbered checklist a new hire could\nfollow. Flag any step that is unclear.",
     "Number four. Turn a messy process into a checklist. Describe how you do a task, in whatever order it comes to mind, "
     "and ask for a numbered checklist a new hire could follow. Asking it to flag unclear steps shows you the gaps in your own process."),
    ("WAY 5", "Get spreadsheet formulas explained",
     "My columns are: A=date, B=client, C=amount.\nWrite a formula that sums amount for one client\nin one month. Explain each part in plain English.",
     "Number five. Get spreadsheet formulas explained. Tell it what is in each column, describe what you want, "
     "and ask it to explain each part in plain English. You get the formula and you actually learn how it works. "
     "Just test it on a few rows you can check by hand."),
    ("YOUR TURN", "Which one will you try first?",
     "Comment your job title below and I'll\nbuild a custom prompt for it.\n\nSubscribe for a new A.I. workflow every week.",
     "That's five ways to use A.I. at work this week. Pick one and try it on a real task today. "
     "If you comment your job title below, I'll build a custom prompt for it in a future video. "
     "And if this was useful, subscribe, because I post a new A.I. workflow every week. Thanks for watching."),
]


def font(name, size):
    return ImageFont.truetype(F.format(name), size)


def render_slide(i, kicker, headline, box):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 24, H], fill=ACCENT)
    y = 110
    if kicker:
        d.text((120, y), kicker, font=font("Bold", 40), fill=ACCENT)
        y += 80
    hf = font("ExtraBold", 96 if i else 120)
    for line in textwrap.wrap(headline, width=24 if i else 20):
        d.text((120, y), line, font=hf, fill=FG)
        y += 120 if i else 150
    if box:
        y += 40
        mf = ImageFont.truetype(MONO, 38)
        lines = box.split("\n")
        bh = len(lines) * 58 + 80
        d.rounded_rectangle([120, y, W - 120, y + bh], radius=24, fill=BOX)
        d.text((160, y + 24), "PROMPT" if kicker.startswith("WAY") else "", font=font("Bold", 26), fill=MUTED)
        ty = y + 56 if kicker.startswith("WAY") else y + 40
        for ln in lines:
            d.text((160, ty), ln, font=mf, fill=FG)
            ty += 58
    d.text((120, H - 80), "AI at Work  |  new workflow every week", font=font("Medium", 30), fill=MUTED)
    path = TMP / f"slide_{i}.png"
    img.save(path)
    return path


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}"


def main():
    kokoro = Kokoro(str(MODELS / "kokoro.onnx"), str(MODELS / "voices.bin"))
    clips, srt, t = [], [], 0.0
    n = 1
    for i, (kicker, headline, box, narr) in enumerate(SCENES):
        slide = render_slide(i, kicker, headline, box)
        samples, sr = kokoro.create(narr, voice="am_michael", speed=1.0, lang="en-us")
        pad = np.zeros(int(sr * 0.6), dtype=samples.dtype)
        samples = np.concatenate([samples, pad])
        wav = TMP / f"vo_{i}.wav"
        sf.write(wav, samples, sr)
        dur = len(samples) / sr
        mp4 = TMP / f"clip_{i}.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(slide), "-i", str(wav),
             "-t", f"{dur:.3f}", "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
             "-r", "30", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2", str(mp4)],
            check=True)
        clips.append(mp4)
        # captions: split narration into sentences, spread by character count
        sents = [s.strip() for s in narr.replace("?", ".").split(".") if s.strip()]
        total = sum(len(s) for s in sents)
        ct = t
        for s in sents:
            sd = (dur - 0.6) * len(s) / total
            srt.append(f"{n}\n{srt_time(ct)} --> {srt_time(ct+sd)}\n{s}.\n")
            ct += sd
            n += 1
        t += dur
    lst = TMP / "list.txt"
    lst.write_text("".join(f"file '{c.resolve()}'\n" for c in clips))
    final = OUT / "5-ways-to-use-ai-at-work.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", str(final)], check=True)
    (OUT / "captions.srt").write_text("\n".join(srt))
    Image.open(TMP / "slide_0.png").save(OUT / "thumbnail_draft.png")
    print("done", final, f"{t:.1f}s")


main()
