#!/usr/bin/env python3
"""
CropSense AI: build the demo video (1920x1080, ~3.5 min) from the recorded clips, deck slides and a voice-over.

  python3 scripts/build_video.py [--deck "~/Downloads/CropSense AI — Pitch Deck_1.pdf"] [--voice Rishi]

Inputs:  artifacts/video/NN-*.webm (from scripts/record_demo.cjs), the pitch-deck PDF.
Output:  artifacts/video/cropsense-demo.mp4 (captions as a subtitle track you can switch on/off) and
         cropsense-demo.srt. Pass --burn-captions to draw the captions into the picture instead.
Needs:   ffmpeg, pdftoppm (brew install ffmpeg poppler), macOS `say`, Playwright in solidjs/node_modules.

Each narration line is synthesised on its own, so captions match the audio exactly. A line with a time is placed
at that point of the segment (seconds after the edit below); a line without one follows the previous line.
"""
import argparse, json, os, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VID = ROOT / "artifacts" / "video"
NODE = Path.home() / ".nvm/versions/node/v24.20.0/bin/node"
W, H, FPS, GAP = 1920, 1080, 30, 0.35

# pieces: (start, end, speed) of the raw clip; end None = to the end of the clip.
SEGMENTS = [
    {"id": "01", "slides": [
        (1, ["Our first version of CropSense did too much.",
             "It was built for a different purpose, and it got too complicated for a farmer to use."]),
        (2, ["Then I went to Udaipur and met farmers there.",
             "Small plots, rain-fed fields, advice that never fit their own land, and never in their language.",
             "That's when I realised it had to be rewritten, simple, and built around them."]),
        (5, ["So I rewrote it in three to four days, with Gemini at every step."]),
    ], "fade": (True, False)},
    # Screen captures of the build (cropped from the 28 Sep screen recordings).
    {"id": "01b", "clip": "01b-deep-research.mp4", "label": "Gemini Deep Research", "fade": (False, False),
     "pieces": [(0, 9.0, 2), (9.0, 21.0, 6), (21.0, None, 2.5)],
     "lines": [(0.6, "Gemini Deep Research did the research grunt work: the hackathon brief, government schemes, "
                     "and soil and weather datasets.")]},
    {"id": "01c", "clip": "01c-notebooklm.mp4", "label": "Report → NotebookLM", "fade": (False, False),
     "pieces": [(1.2, None, 1.4)],
     "lines": [(0.4, "Its report went straight into NotebookLM, which turned government reports into our problem "
                     "and data model.")]},
    {"id": "01d", "clip": "01d-antigravity-stitch.mp4", "label": "Antigravity + Stitch MCP", "fade": (False, True),
     "pieces": [(0, None, 3)],
     "lines": [(0.4, "Stitch designed the screens, called by Antigravity's Gemini agents through MCP, "
                     "and those agents turned them into working code.")]},
    {"id": "02", "clip": "02-landing.webm", "label": "CropSense AI · the live app",
     "pieces": [(1.2, None, 1)],
     "lines": [(1.0, "CropSense gives every small farmer advice for their own field, in their own language, "
                     "powered by Gemini 3.8 Flash.")]},
    {"id": "03", "clip": "03-signin-language.webm", "label": "Demo sign-in · English, हिंदी, मराठी, ਪੰਜਾਬੀ",
     "pieces": [(1.0, None, 1)],
     "lines": [(0.8, "Farmers sign in once, or try a demo account."),
               (6.5, "The menus switch to Hindi, Marathi or Punjabi.")]},
    {"id": "04", "clip": "04-register-farm.webm", "label": "Register a farm · pincode → district",
     "pieces": [(2.8, 13.0, 1), (13.0, 23.0, 2.5), (23.0, None, 1)],
     "lines": [(0.8, "Here's a farm near Udaipur."),
               (None, "From just the pincode, we know the state, district and village, "
                      "so the farmer types almost nothing."),
               (15.4, "The farm is saved to their own account, and it works for any district in India.")]},
    {"id": "05", "clip": "05-crop-plan.webm", "label": "365-day crop plan · Gemini 3.8 Flash on Vertex AI",
     "pieces": [(1.2, 14.0, 1), (14.0, 46.0, 8), (46.0, None, 1)],
     "lines": [(0.8, "Now we ask what to grow."),
               (None, "Gemini 3.8 Flash on Vertex AI reads this farm's soil profile and the local weather "
                      "forecast together."),
               (17.0, "It recommends a three-season crop rotation with expected profit per acre, "
                      "and regenerative practices for this field, not the whole state.")]},
    {"id": "06", "clip": "06-diagnose.webm", "label": "Photo diagnosis · Gemini 3.8 Flash multimodal",
     "pieces": [(2.8, 10.0, 1), (10.0, 19.0, 4), (19.0, None, 1)],
     "lines": [(0.8, "When something goes wrong, the farmer just takes a photo."),
               (9.8, "Gemini's multimodal reasoning names the disease, how serious it is, and the treatment."),
               (None, "Pesticides banned in India are removed, and every chemical comes with a label-safety note.")]},
    {"id": "07", "clip": "07-voice.webm", "label": "Ask CropSense · Gemini 3.5 Flash-Lite",
     "pieces": [(2.8, None, 1)],
     "lines": [(0.8, "Many farmers would rather ask than search."),
               (None, "Gemini 3.5 Flash-Lite looks at this farmer's own farm before it answers, "
                      "in their own language."),
               (13.6, "Crops, varieties and sowing times come back in a simple table.")]},
    {"id": "08", "clip": "08-alerts-market.webm", "label": "Alerts & mandi · next screens",
     "pieces": [(2.8, None, 1)],
     "lines": [(0.8, "Advice doesn't stop at planting."),
               (None, "Weather and pest alerts, mandi prices and buyers after harvest are the next screens "
                      "we're wiring up.")]},
    {"id": "09", "slides": [
        (6, ["It's Gemini on Google Cloud: Vertex AI, Cloud Run, Cloud SQL and Firebase, deployed with one command."]),
        (12, ["Any state can pilot it in a district within weeks."]),
        (13, ["Rewritten with Gemini, running on Gemini, ready for every farmer in India."]),
    ]},
]


def run(*cmd, **kw):
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


def duration(path):
    out = run("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path,
              capture_output=True, text=True).stdout
    return float(out.strip())


def render_overlays(items, out_dir):
    """items: [(name, kind, text)] → PNGs (transparent) sized to the caption pill / label chip."""
    html = """<html><head><style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;700&display=swap');
body{margin:0;background:transparent;font-family:'Plus Jakarta Sans',sans-serif}
.cap{display:inline-block;max-width:1500px;padding:16px 30px;border-radius:18px;background:rgba(10,30,22,.86);
color:#fff;font-size:38px;line-height:1.35;font-weight:500;text-align:center}
.lab{display:inline-flex;align-items:center;gap:14px;padding:14px 26px;border-radius:999px;background:#065f46;
color:#ecfdf5;font-size:30px;font-weight:700;box-shadow:0 6px 24px rgba(0,0,0,.25)}
.lab i{width:12px;height:12px;border-radius:50%;background:#fbbf24;display:inline-block}
</style></head><body><div id=x></div></body></html>"""
    js = f"""
const {{chromium}} = require({json.dumps(str(ROOT / 'solidjs/node_modules/playwright'))});
const items = {json.dumps(items)};
(async () => {{
  const b = await chromium.launch(); const p = await b.newPage({{viewport: {{width: 1920, height: 400}}}});
  await p.setContent({json.dumps(html)}, {{waitUntil: 'networkidle'}});
  for (const [name, kind, text] of items) {{
    await p.evaluate(([k, t]) => {{
      const x = document.getElementById('x');
      x.innerHTML = k === 'cap' ? '<div class=cap></div>' : '<div class=lab><i></i><span></span></div>';
      (k === 'cap' ? x.firstChild : x.querySelector('span')).textContent = t;
    }}, [kind, text]);
    await p.locator('#x > div').screenshot({{path: {json.dumps(str(out_dir))} + '/' + name + '.png', omitBackground: true}});
  }}
  await b.close();
}})();"""
    f = out_dir / "render.cjs"
    f.write_text(js)
    run(NODE, f)


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", default=str(Path.home() / "Downloads/CropSense AI — Pitch Deck_1.pdf"))
    ap.add_argument("--voice", default="Rishi")
    ap.add_argument("--rate", default="165")
    ap.add_argument("--burn-captions", action="store_true", help="draw captions into the picture")
    args = ap.parse_args()

    tmp = Path(tempfile.mkdtemp(prefix="cropsense-video-"))
    print("work dir:", tmp)
    run("pdftoppm", "-png", "-r", "144", "-scale-to-x", W, "-scale-to-y", H, args.deck, tmp / "slide")
    slide = lambda n: next(tmp.glob(f"slide-*{n:02d}.png"))

    # 1. Voice-over, one file per line.
    lines = []  # (seg_id, idx, text, path, dur)
    for seg in SEGMENTS:
        texts = [t for _, ts in seg["slides"] for t in ts] if "slides" in seg else [t for _, t in seg["lines"]]
        for i, text in enumerate(texts):
            p = tmp / f"vo-{seg['id']}-{i}.aiff"
            run("say", "-v", args.voice, "-r", args.rate, "-o", p, text)
            lines.append((seg["id"], i, text, p, duration(p)))
    vo = {(s, i): (t, p, d) for s, i, t, p, d in lines}

    # 2. Captions and labels.
    overlays = [(f"cap-{s}-{i}", "cap", t) for s, i, t, _, _ in lines]
    overlays += [(f"lab-{s['id']}", "lab", s["label"]) for s in SEGMENTS if s.get("label")]
    render_overlays(overlays, tmp)

    # 3. One mp4 per segment.
    parts, srt, clock = [], [], 0.0
    for seg in SEGMENTS:
        sid = seg["id"]
        n = sum(len(ts) for _, ts in seg["slides"]) if "slides" in seg else len(seg["lines"])
        timed, t = [], 0.0
        inputs, vf = [], []
        if "slides" in seg:
            k, chunks = 0, []
            for num, ts in seg["slides"]:
                start = t
                t += 0.7
                for _ in ts:
                    timed.append(t)
                    t += vo[(sid, k)][2] + GAP
                    k += 1
                t += 0.5
                chunks.append((slide(num), t - start))
            for i, (img, d) in enumerate(chunks):
                inputs += ["-loop", "1", "-framerate", FPS, "-t", f"{d:.3f}", "-i", img]
                vf.append(f"[{i}:v]scale={W}:{H},setsar=1,fps={FPS},format=yuv420p[s{i}]")
            vf.append("".join(f"[s{i}]" for i in range(len(chunks))) + f"concat=n={len(chunks)}:v=1:a=0[base]")
            total = t
            nv = len(chunks)
        else:
            src = VID / seg["clip"]
            clip_len = duration(src)
            inputs += ["-i", src]
            pieces = []
            for j, (a, b, sp) in enumerate(seg["pieces"]):
                b = clip_len if b is None else b
                vf.append(f"[0:v]trim={a}:{b},setpts=(PTS-STARTPTS)/{sp},fps={FPS},scale={W}:{H},setsar=1[p{j}]")
                pieces.append(f"[p{j}]")
            vlen = sum(((clip_len if b is None else b) - a) / sp for a, b, sp in seg["pieces"])
            for k, (at, _) in enumerate(seg["lines"]):
                t = max(t, at) if at is not None else t
                timed.append(t)
                t += vo[(sid, k)][2] + GAP
            total = max(vlen, t + 1.2)
            vf.append("".join(pieces) + f"concat=n={len(pieces)}:v=1:a=0,"
                      f"tpad=stop_mode=clone:stop_duration={total - vlen + 0.1:.3f},format=yuv420p[base]")
            nv = 1

        # captions + label overlays
        cur, idx = "[base]", nv
        for k in range(n):
            a, b = timed[k], timed[k] + vo[(sid, k)][2] + 0.25
            if args.burn_captions:
                inputs += ["-i", tmp / f"cap-{sid}-{k}.png"]
                vf.append(f"{cur}[{idx}:v]overlay=x=(W-w)/2:y=H-h-48:enable='between(t,{a:.3f},{b:.3f})'[o{idx}]")
                cur, idx = f"[o{idx}]", idx + 1
            srt.append((clock + a, clock + b, vo[(sid, k)][0]))
        if seg.get("label"):
            inputs += ["-i", tmp / f"lab-{sid}.png"]
            vf.append(f"{cur}[{idx}:v]overlay=x=48:y=H-h-190:enable='between(t,0.4,4.6)'[o{idx}]")
            cur, idx = f"[o{idx}]", idx + 1
        fin, fout = seg.get("fade", (True, True))
        fades = ([f"fade=t=in:st=0:d=0.35"] if fin else []) + ([f"fade=t=out:st={total - 0.35:.3f}:d=0.35"] if fout else [])
        vf.append(f"{cur}{','.join(fades) or 'null'}[v]")

        # audio: every line delayed to its slot, then mixed
        for k in range(n):
            inputs += ["-i", vo[(sid, k)][1]]
        amix = []
        for k in range(n):
            ms = int(timed[k] * 1000)
            vf.append(f"[{idx + k}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms}[a{k}]")
            amix.append(f"[a{k}]")
        vf.append("".join(amix) + f"amix=inputs={n}:normalize=0:duration=longest,apad,atrim=0:{total:.3f}[a]")

        out = tmp / f"seg-{sid}.mp4"
        run("ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(vf), "-map", "[v]", "-map", "[a]",
            "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-r", FPS,
            "-c:a", "aac", "-b:a", "160k", out)
        print(f"  {sid}  {total:5.1f}s")
        parts.append(out)
        clock += total

    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in parts))
    final, srt_file = VID / "cropsense-demo.mp4", VID / "cropsense-demo.srt"
    srt_file.write_text(
        "".join(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{t}\n\n" for i, (a, b, t) in enumerate(srt, 1)))
    # Soft subtitles: a separate English track players can switch on and off (QuickTime, VLC, YouTube upload).
    run("ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", srt_file,
        "-map", "0:v", "-map", "0:a", "-map", "1:s", "-c", "copy", "-c:s", "mov_text",
        "-metadata:s:s:0", "language=eng", "-metadata:s:s:0", "title=English",
        "-disposition:s:0", "0" if args.burn_captions else "default", "-movflags", "+faststart", final)
    m, s = divmod(duration(final), 60)
    print(f"done: {final}  {int(m)}:{s:04.1f}")


if __name__ == "__main__":
    main()
