from django.urls import path
from . import views

urlpatterns = [
    path('',                    views.home,             name='home'),
    path('about/',              views.about,            name='about'),
    path('detection/',          views.detection,        name='detection'),
    path('camera/',             views.camera,           name='camera'),
    path('camera/predict/',     views.camera_predict,   name='camera_predict'),
    path('history/',            views.history,          name='history'),
    path('history/delete/<int:pk>/', views.delete_prediction, name='delete_prediction'),
    path('contact/',            views.contact,          name='contact'),
    path('faq/',                views.faq,              name='faq'),
]