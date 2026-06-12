from django.apps import AppConfig


class DetectorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'detector'

    def ready(self):
        # Warm up the model in a background thread so the first request isn't slow.
        import threading
        def warmup():
            try:
                from .predict import _load_model
                _load_model()
            except Exception:
                pass
        threading.Thread(target=warmup, daemon=True).start()