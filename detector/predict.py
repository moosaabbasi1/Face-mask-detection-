"""
predict.py — Model loading and prediction logic for Face Mask Detection.
"""
import os
import logging
import numpy as np
from pathlib import Path
from PIL import Image
import io

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
IMG_SIZE    = (224, 224)          # ✅ FIXED: must match training size
CLASS_NAMES = ['incorrect_mask', 'with_mask', 'without_mask']  # alphabetical (Keras default)

# Human-readable labels for display
LABEL_MAP = {
    'with_mask':      'Mask',
    'without_mask':   'No Mask',
    'incorrect_mask': 'Incorrect Mask',
}

CLASS_COLORS = {
    'with_mask':      '#10B981',   # green
    'without_mask':   '#EF4444',   # red
    'incorrect_mask': '#F59E0B',   # orange
}

# ── Lazy-loaded model ─────────────────────────────────────────────────────────
_model = None


def _load_model():
    global _model
    if _model is not None:
        return _model

    try:
        import tensorflow as tf
    except ImportError:
        logger.error("TensorFlow is not installed.")
        return None

    base = Path(__file__).resolve().parent.parent

    for candidate in [
        base / 'ml_models' / 'face_mask_cnn.keras',
        base / 'ml_models' / 'face_mask_cnn.h5',
        base / 'face_mask_cnn.keras',
        base / 'face_mask_cnn.h5',
    ]:
        if candidate.exists():
            try:
                logger.info("Loading model from %s …", candidate)
                _model = tf.keras.models.load_model(str(candidate))
                logger.info("Model loaded  — output shape: %s", _model.output_shape)
                return _model
            except Exception as exc:
                logger.warning("Failed to load %s: %s", candidate, exc)

    logger.error("No model file found in ml_models/")
    return None


def preprocess_image(image_source) -> np.ndarray:
    """Return a (1, 224, 224, 3) float32 array normalised to [0, 1]."""
    if isinstance(image_source, (str, Path)):
        img = Image.open(image_source)
    elif isinstance(image_source, bytes):
        img = Image.open(io.BytesIO(image_source))
    elif isinstance(image_source, io.BytesIO):
        img = Image.open(image_source)
    elif isinstance(image_source, Image.Image):
        img = image_source
    else:
        img = Image.open(image_source)

    img = img.convert('RGB')
    img = img.resize(IMG_SIZE)                          # ✅ 224×224
    arr = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)


def predict(image_source) -> dict:
    """
    Returns:
        success     bool
        raw_label   str   ('with_mask' | 'without_mask' | 'incorrect_mask')
        prediction  str   ('Mask' | 'No Mask' | 'Incorrect Mask')  ← for DB + display
        confidence  float (0–100)
        color       str   hex color
        error       str   only when success=False
    """
    model = _load_model()
    if model is None:
        return {'success': False, 'error': 'Model could not be loaded.'}

    try:
        arr = preprocess_image(image_source)
        raw = model.predict(arr, verbose=0)

        if raw.shape[-1] == 1:
            # Binary sigmoid fallback
            prob = float(raw[0][0])
            raw_label  = 'with_mask' if prob >= 0.5 else 'without_mask'
            confidence = prob * 100 if prob >= 0.5 else (1 - prob) * 100
        else:
            # Softmax 3-class  ✅
            idx       = int(np.argmax(raw[0]))
            raw_label = CLASS_NAMES[idx] if idx < len(CLASS_NAMES) else f'class_{idx}'
            confidence = float(np.max(raw[0])) * 100

        return {
            'success':    True,
            'raw_label':  raw_label,
            'prediction': LABEL_MAP.get(raw_label, raw_label),   # ✅ human label
            'confidence': round(confidence, 2),
            'color':      CLASS_COLORS.get(raw_label, '#6B7280'),
        }

    except Exception as exc:
        logger.exception("Prediction error: %s", exc)
        return {'success': False, 'error': f'Prediction failed: {exc}'}