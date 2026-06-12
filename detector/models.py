from django.db import models
from django.utils import timezone


class Prediction(models.Model):
    image       = models.ImageField(upload_to='predictions/%Y/%m/%d/')
    prediction  = models.CharField(max_length=30)   # ✅ wider — 'Incorrect Mask' = 14 chars
    confidence  = models.FloatField()
    source      = models.CharField(
                      max_length=20, default='upload',
                      choices=[('upload', 'Upload'), ('camera', 'Camera')]
                  )
    created_at  = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.prediction} ({self.confidence:.1f}%) — {self.created_at:%Y-%m-%d %H:%M}"

    @property
    def badge_color(self):
        # ✅ FIXED: handles all 3 classes
        return {
            'Mask':           'success',
            'No Mask':        'danger',
            'Incorrect Mask': 'warning',
        }.get(self.prediction, 'secondary')

    @property
    def badge_icon(self):
        return {
            'Mask':           'shield-check',
            'No Mask':        'shield-x',
            'Incorrect Mask': 'shield-exclamation',
        }.get(self.prediction, 'question-circle')


class ContactMessage(models.Model):
    name       = models.CharField(max_length=100)
    email      = models.EmailField()
    subject    = models.CharField(max_length=200, blank=True)
    message    = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} <{self.email}> — {self.created_at:%Y-%m-%d}"