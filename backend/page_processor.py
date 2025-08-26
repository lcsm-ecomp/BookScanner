import cv2
import numpy as np
from typing import Tuple, Dict

def _order_points(pts: np.ndarray) -> np.ndarray:
    # pts shape: (4,2)
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1).reshape(-1)
    tl = pts[np.argmin(s)]
    br = pts[np.argmax(s)]
    tr = pts[np.argmin(diff)]
    bl = pts[np.argmax(diff)]
    return np.array([tl, tr, br, bl], dtype=np.float32)

def _four_point_transform(image: np.ndarray, pts: np.ndarray) -> np.ndarray:
    rect = _order_points(pts.astype(np.float32))
    (tl, tr, br, bl) = rect
    # Compute width and height of the new image
    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxWidth = int(max(widthA, widthB))
    maxHeight = int(max(heightA, heightB))
    maxWidth = max(maxWidth, 600)    # mínimos para qualidade
    maxHeight = max(maxHeight, 800)

    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype=np.float32)

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight), flags=cv2.INTER_CUBIC)
    return warped

def _largest_quad_contour(edged: np.ndarray) -> np.ndarray:
    # encontra contornos externos
    cnts, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)  # epsilon 2% do perímetro
        if len(approx) == 4 and cv2.isContourConvex(approx):
            return approx.reshape(4, 2)
    return None

def process_page(jpeg_bytes: np.ndarray) -> Tuple[np.ndarray, Dict]:
    """
    Recebe um buffer (np.uint8) de uma imagem JPEG e retorna:
      - imagem BGR recortada/retificada (np.ndarray)
      - metadados (dict)
    """
    image = cv2.imdecode(jpeg_bytes, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Falha ao decodificar imagem")
    orig = image.copy()

    # Pré-processamento
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5,5), 0)

    # Bordas
    v = np.median(gray)
    lower = int(max(0, 0.66 * v))
    upper = int(min(255, 1.33 * v))
    edged = cv2.Canny(gray, lower, upper)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
    edged = cv2.dilate(edged, kernel, iterations=1)
    edged = cv2.erode(edged, kernel, iterations=1)

    quad = _largest_quad_contour(edged)

    meta = {"method": "approx-poly" if quad is not None else "min-area-rect"}

    if quad is None:
        # Fallback: usa retângulo mínimo
        cnts, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not cnts:
            # sem contornos: retorna original
            return orig, {"method": "original"}
        c = max(cnts, key=cv2.contourArea)
        rect = cv2.minAreaRect(c)
        box = cv2.boxPoints(rect)  # 4x2 float
        quad = np.int0(box)

    warped = _four_point_transform(orig, quad.astype(np.float32))
    return warped, meta
