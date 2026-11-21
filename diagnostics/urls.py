
from django.urls import path
from . import views

app_name = 'diagnostics'

urlpatterns = [

    # Выбор предмета и запуск диагностики
    path(
        '',
        views.start_diagnostic,
        name='start'
    ),

    # Прохождение теста
    path(
        'take/<int:attempt_id>/',
        views.take_diagnostic,
        name='take'
    ),

    # Просмотр результатов
    path(
        'result/<int:attempt_id>/',
        views.diagnostic_result,
        name='result'
    ),

    # История диагностик
    path(
        'history/',
        views.diagnostic_history,
        name='history'
    ),

    # Персональная дорожная карта
    path(
        'roadmap/',
        views.roadmap_view,
        name='roadmap'
    ),

]
