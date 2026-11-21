
import os
import django

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'config.settings'
)

django.setup()

from django.contrib.auth import get_user_model
from diagnostics.roadmap import build_roadmap

User = get_user_model()

# Получаем пользователя
user = User.objects.get(username='Kirill')

# Строим дорожную карту
result = build_roadmap(user)

print('\n========== MATHBANK ROADMAP TEST ==========\n')

print(f'Пользователь: {user.username}')
print(f'Всего тем: {len(result)}\n')

for item in result:
    print(f"ШАГ {item['study_order']}: {item['topic']}")
    print(f"Предмет: {item['subject_name']}")
    print(f"Всего заданий: {item['total']}")
    print(f"Отвечено: {item['answered']}")
    print(f"Правильных: {item['correct']}")
    print(f"Ошибок: {item['wrong']}")
    print(f"Пропущено: {item['skipped']}")
    print(f"Результат: {item['percentage']}%")
    print(f"Приоритет: {item['priority']}")
    print(f"Зависимости: {item['dependencies']}")
    print(f"Что мешает: {item['blocking_topics']}")
    print(f"Статус: {item['status_label']}")
    print(f"Рекомендация: {item['recommendation']}")
    print(f"Причина: {item['study_reason']}")
    print('-' * 60)

print('\n========== TEST COMPLETED ==========\n')
