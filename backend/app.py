from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
import re, time, uuid, pathlib
import numpy as np
import cv2
from page_processor import process_page

app = FastAPI(title="Comics Scanner API")

# CORS liberado para testes locais (ajuste em produção)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = pathlib.Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

_slug_re = re.compile(r"[^a-z0-9]+")

def slugify(name: str) -> str:
    s = name.strip().lower()
    s = _slug_re.sub("-", s)
    s = s.strip("-")
    return s or "sem-nome"

@app.get("/api/health")
def health():
    return {"ok": True, "time": time.time()}

@app.post("/api/upload")
async def upload_pages(
    title: str = Form(...),
    images: List[UploadFile] = File(...)
):
    slug = slugify(title)
    base_dir = DATA_DIR / slug
    raw_dir = base_dir / "raw"
    pages_dir = base_dir / "pages"
    raw_dir.mkdir(parents=True, exist_ok=True)
    pages_dir.mkdir(parents=True, exist_ok=True)

    saved = []
    page_idx = len(list(pages_dir.glob("page-*.jpg")))  # continua numeração
    for img in images:
        raw_bytes = await img.read()
        # Salva original
        ts = int(time.time() * 1000)
        raw_name = f"raw-{ts}-{uuid.uuid4().hex[:6]}.jpg"
        raw_path = raw_dir / raw_name
        with open(raw_path, "wb") as f:
            f.write(raw_bytes)

        # Processa (detecção de borda + warp)
        try:
            page_bgr, meta = process_page(np.frombuffer(raw_bytes, dtype=np.uint8))
        except Exception as e:
            # Se falhar, armazena original também em pages como fallback
            page_bgr = cv2.imdecode(np.frombuffer(raw_bytes, np.uint8), cv2.IMREAD_COLOR)
            meta = {"note": f"fallback_original: {e!r}"}

        # Garantir orientação retrato
        h, w = page_bgr.shape[:2]
        if w > h:
            page_bgr = cv2.rotate(page_bgr, cv2.ROTATE_90_CLOCKWISE)
            h, w = page_bgr.shape[:2]
            meta["rotated_to_portrait"] = True

        page_idx += 1
        page_name = f"page-{page_idx:03d}.jpg"
        page_path = pages_dir / page_name
        # Salvar JPEG com qualidade 95
        cv2.imwrite(str(page_path), page_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 95])

        saved.append({
            "raw": str(raw_path.relative_to(DATA_DIR)),
            "page": str(page_path.relative_to(DATA_DIR)),
            "w": int(w), "h": int(h),
            "meta": meta,
        })

    return JSONResponse({
        "folder": str(base_dir.relative_to(DATA_DIR)),
        "saved_count": len(saved),
        "items": saved
    })
