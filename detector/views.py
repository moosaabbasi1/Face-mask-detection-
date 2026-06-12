import base64
import io
import json
import logging
from datetime import datetime

from django.contrib import messages
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from PIL import Image

from .forms import CameraForm, ContactForm, ImageUploadForm
from .models import ContactMessage, Prediction
from .predict import predict

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _dashboard_stats():
    # ✅ FIXED: use the human labels that get stored in the DB
    total          = Prediction.objects.count()
    mask           = Prediction.objects.filter(prediction='Mask').count()
    no_mask        = Prediction.objects.filter(prediction='No Mask').count()
    incorrect_mask = Prediction.objects.filter(prediction='Incorrect Mask').count()
    return {
        'total':          total,
        'mask':           mask,
        'no_mask':        no_mask,
        'incorrect_mask': incorrect_mask,
    }


# ── Pages ─────────────────────────────────────────────────────────────────────

def home(request):
    stats  = _dashboard_stats()
    recent = Prediction.objects.all()[:6]
    return render(request, 'detector/home.html', {'stats': stats, 'recent': recent})


def about(request):
    return render(request, 'detector/about.html')


def faq(request):
    faqs = [
        {
            'q': 'What types of images does the system accept?',
            'a': 'JPEG, PNG, and WebP images up to 5 MB. For best results use a clear '
                 'frontal face photo with good lighting.',
        },
        {
            'q': 'How accurate is the face mask detector?',
            'a': 'The CNN model was trained on thousands of labelled images and typically '
                 'achieves 95–98% accuracy on held-out test data.',
        },
        {
            'q': 'Is my image stored permanently?',
            'a': 'Uploaded images are saved to the local media folder. '
                 'You can delete records from the History page at any time.',
        },
        {
            'q': 'Can I use the live camera feature on mobile?',
            'a': 'Yes. The webcam page uses the standard MediaDevices API supported '
                 'on all modern mobile browsers over HTTPS.',
        },
        {
            'q': 'What deep learning framework powers the model?',
            'a': 'The model was built and trained with TensorFlow / Keras and is served '
                 'server-side by the Django backend.',
        },
        {
            'q': 'How do I report a wrong prediction?',
            'a': 'Use the Contact page to send us feedback with the image and prediction received.',
        },
    ]
    return render(request, 'detector/faq.html', {'faqs': faqs})


# ── Detection ─────────────────────────────────────────────────────────────────

def detection(request):
    form   = ImageUploadForm()
    result = None

    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded = request.FILES['image']
            result   = predict(uploaded)

            if result['success']:
                uploaded.seek(0)
                record = Prediction.objects.create(
                    image      = uploaded,
                    prediction = result['prediction'],   # 'Mask' | 'No Mask' | 'Incorrect Mask'
                    confidence = result['confidence'],
                    source     = 'upload',
                )
                result['record_id'] = record.pk

    return render(request, 'detector/detection.html', {'form': form, 'result': result})


def camera(request):
    return render(request, 'detector/camera.html')


@csrf_exempt
@require_POST
def camera_predict(request):
    try:
        body     = json.loads(request.body)
        img_data = body.get('image_data', '')

        if ',' in img_data:
            img_data = img_data.split(',', 1)[1]

        img_bytes = base64.b64decode(img_data)
        pil_image = Image.open(io.BytesIO(img_bytes))
        result    = predict(pil_image)

        if result['success']:
            buf = io.BytesIO()
            pil_image.save(buf, format='JPEG', quality=85)
            buf.seek(0)
            filename = f"camera_{datetime.now():%Y%m%d_%H%M%S}.jpg"
            record   = Prediction(
                prediction = result['prediction'],
                confidence = result['confidence'],
                source     = 'camera',
            )
            record.image.save(filename, ContentFile(buf.read()), save=True)
            result['record_id'] = record.pk

        return JsonResponse(result)

    except Exception as exc:
        logger.exception("camera_predict error: %s", exc)
        return JsonResponse({'success': False, 'error': str(exc)}, status=400)


# ── History ───────────────────────────────────────────────────────────────────

def history(request):
    qs = Prediction.objects.all()

    search      = request.GET.get('search', '').strip()
    filter_type = request.GET.get('filter', '')

    if search:
        qs = qs.filter(prediction__icontains=search)

    # ✅ FIXED: filter choices now match all 3 stored labels
    valid_filters = ('Mask', 'No Mask', 'Incorrect Mask')
    if filter_type in valid_filters:
        qs = qs.filter(prediction=filter_type)

    paginator = Paginator(qs, 12)
    page_obj  = paginator.get_page(request.GET.get('page'))
    stats     = _dashboard_stats()

    return render(request, 'detector/history.html', {
        'page_obj': page_obj,
        'stats':    stats,
        'search':   search,
        'filter':   filter_type,
    })


def delete_prediction(request, pk):
    record = get_object_or_404(Prediction, pk=pk)
    if request.method == 'POST':
        record.image.delete(save=False)
        record.delete()
        messages.success(request, 'Prediction record deleted.')
    return redirect('history')


# ── Contact ───────────────────────────────────────────────────────────────────

def contact(request):
    form = ContactForm()
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your message has been sent!")
            return redirect('contact')
    return render(request, 'detector/contact.html', {'form': form})