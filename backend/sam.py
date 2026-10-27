# backend/sam.py

import os, base64, io, re, uuid
from PIL import Image, ImageDraw
from dotenv import load_dotenv
from backend.muse import MUSE_MODE
import pathlib
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent  # repo root
UPLOAD_ORIG = str(BASE_DIR / "uploads" / "original")
UPLOAD_REDACTED = str(BASE_DIR / "uploads" / "redacted")

load_dotenv()

os.makedirs(UPLOAD_ORIG, exist_ok=True)
os.makedirs(UPLOAD_REDACTED, exist_ok=True)


def redact_image(image_bytes: bytes, prompt: str = "face") -> dict:
    """Detect prompt matches in image, black them out, return redacted path + boxes."""
    image_id = str(uuid.uuid4())
    orig_path = os.path.join(UPLOAD_ORIG, f"{image_id}.jpg")
    red_path = os.path.join(UPLOAD_REDACTED, f"{image_id}.jpg")

    with open(orig_path, "wb") as f:
        f.write(image_bytes)

    if MUSE_MODE == "mock":
        boxes = _mock_boxes()
    else:
        boxes = _live_sam_boxes(image_bytes, prompt)

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    draw = ImageDraw.Draw(img)
    for b in boxes:
        draw.rectangle([b["x1"], b["y1"], b["x2"], b["y2"]], fill="black")
    img.save(red_path, "JPEG")

    return {
        "original_path": orig_path,     # never served to any client
        "redacted_path": red_path,      # the only one served
        "boxes": boxes,
        "prompt": prompt,
    }


def _mock_boxes():
    # Deterministic mock for dev: a single box roughly where a face usually is
    return [{"x1": 80, "y1": 60, "x2": 180, "y2": 160}]


def _live_sam_boxes(image_bytes: bytes, prompt: str) -> list:
    from openai import OpenAI
    client = OpenAI(
        base_url="https://api.meta.ai/v1",
        api_key=os.environ["MODEL_API_KEY"],
    )
    b64 = base64.b64encode(image_bytes).decode()
    resp = client.responses.create(
        model="sam-3.1",
        input=[{
            "type": "message",
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                {"type": "input_image", "image_url": f"data:image/jpeg;base64,{b64}"},
            ],
        }],
    )
    return _parse_boxes(resp.output_text)


def _parse_boxes(output: str) -> list:
    """Minimal parser for SAM's special-token output."""
    boxes = []
    for m in re.finditer(r"\|box;x1=([\d.]+);y1=([\d.]+);x2=([\d.]+);y2=([\d.]+)\|", output):
        x1, y1, x2, y2 = map(float, m.groups())
        boxes.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2})
    return boxes