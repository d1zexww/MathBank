
from collections import defaultdict

from .models import DiagnosticAnswer, DiagnosticQuestion
from .topic_dependencies import TOPIC_DEPENDENCIES


def build_roadmap(user, subject=None):
    answers = DiagnosticAnswer.objects.filter(
        attempt__user=user,
        attempt__is_completed=True
    ).select_related(
        'attempt',
        'question'
    )

    if subject:
        answers = answers.filter(
            attempt__subject=subject
        )

    subject_labels = dict(DiagnosticQuestion.SUBJECT_CHOICES)

    topic_data = defaultdict(lambda: {
        'total': 0,
        'correct': 0,
        'wrong': 0,
        'skipped': 0,
    })

    # 1. Собираем статистику
    for answer in answers:
        subject_code = answer.attempt.subject
        topic_name = answer.question.topic or 'Без темы'

        data = topic_data[(subject_code, topic_name)]
        data['total'] += 1

        user_answer = (answer.user_answer or '').strip()

        if not user_answer:
            data['skipped'] += 1
        elif answer.is_correct:
            data['correct'] += 1
        else:
            data['wrong'] += 1

    roadmap = []

    # 2. Определяем уровень знаний
    for (subject_code, topic_name), data in topic_data.items():
        answered = data['correct'] + data['wrong']

        percentage = (
            round(data['correct'] / answered * 100)
            if answered else 0
        )

        if answered < 5:
            priority = 'insufficient_data'
        elif percentage < 50:
            priority = 'high'
        elif percentage < 75:
            priority = 'medium'
        else:
            priority = 'low'

        roadmap.append({
            'subject': subject_code,
            'subject_name': subject_labels.get(
                subject_code,
                subject_code
            ),
            'topic': topic_name,
            'total': data['total'],
            'answered': answered,
            'correct': data['correct'],
            'wrong': data['wrong'],
            'skipped': data['skipped'],
            'percentage': percentage,
            'priority': priority,
        })

    # 3. Создаём поиск тем
    topic_lookup = {
        (item['subject'], item['topic']): item
        for item in roadmap
    }

    # 4. Анализируем зависимости
    for item in roadmap:
        dependencies = TOPIC_DEPENDENCIES.get(
            item['topic'],
            []
        )

        blocking_topics = []
        uncertain_dependencies = []

        for dependency in dependencies:
            dependency_item = topic_lookup.get(
                (item['subject'], dependency)
            )

            # Нет результатов диагностики по предварительной теме
            if dependency_item is None:
                uncertain_dependencies.append(dependency)
                continue

            # По предварительной теме пока недостаточно ответов
            if dependency_item['priority'] == 'insufficient_data':
                uncertain_dependencies.append(dependency)

            # Предварительная тема требует повторения
            elif dependency_item['priority'] in ['high', 'medium']:
                blocking_topics.append(dependency)

        item['dependencies'] = dependencies
        item['blocking_topics'] = blocking_topics
        item['uncertain_dependencies'] = uncertain_dependencies

        if blocking_topics:
            item['study_reason'] = (
                'Сначала рекомендуется повторить: '
                + ', '.join(blocking_topics)
            )

        elif uncertain_dependencies:
            item['study_reason'] = (
                'Недостаточно данных по предварительным темам: '
                + ', '.join(uncertain_dependencies)
            )

        elif dependencies:
            item['study_reason'] = (
                'По предварительным темам нет выявленных проблем.'
            )

        else:
            item['study_reason'] = (
                'Для этой темы не заданы предварительные темы.'
            )

    # 5. Определяем порядок приоритета
    priority_order = {
        'high': 0,
        'medium': 1,
        'insufficient_data': 2,
        'low': 3,
    }

    def sort_key(item):
        return (
            priority_order[item['priority']],
            item['percentage'],
            item['topic']
        )

    # 6. Строим последовательность с учётом зависимостей
    outgoing = {
        (item['subject'], item['topic']): []
        for item in roadmap
    }

    indegree = {
        (item['subject'], item['topic']): 0
        for item in roadmap
    }

    for item in roadmap:
        current_key = (item['subject'], item['topic'])

        for dependency in item['dependencies']:
            dependency_key = (item['subject'], dependency)

            if dependency_key not in topic_lookup:
                continue

            outgoing[dependency_key].append(current_key)
            indegree[current_key] += 1

    ready = [
        item for item in roadmap
        if indegree[(item['subject'], item['topic'])] == 0
    ]

    ready.sort(key=sort_key)

    ordered_roadmap = []

    while ready:
        current = ready.pop(0)
        ordered_roadmap.append(current)

        current_key = (current['subject'], current['topic'])

        for next_key in outgoing[current_key]:
            indegree[next_key] -= 1

            if indegree[next_key] == 0:
                ready.append(topic_lookup[next_key])
                ready.sort(key=sort_key)

    # Защита от циклических зависимостей
    if len(ordered_roadmap) < len(roadmap):
        ordered_keys = {
            (item['subject'], item['topic'])
            for item in ordered_roadmap
        }

        remaining = [
            item for item in roadmap
            if (item['subject'], item['topic']) not in ordered_keys
        ]

        remaining.sort(key=sort_key)
        ordered_roadmap.extend(remaining)

    # 7. Формируем рекомендации
    for index, item in enumerate(ordered_roadmap, start=1):
        item['study_order'] = index

        if item['blocking_topics']:
            if item['priority'] == 'insufficient_data':
                item['status_label'] = (
                    'Сначала повтори базу'
                )
                item['recommendation'] = (
                    'Повтори предварительные темы: '
                    + ', '.join(item['blocking_topics'])
                    + '. Затем пройди дополнительные задания.'
                )
            else:
                item['status_label'] = (
                    'Сначала изучи базовые темы'
                )
                item['recommendation'] = (
                    'Перед этой темой повтори: '
                    + ', '.join(item['blocking_topics'])
                )

        elif item['uncertain_dependencies']:
            item['status_label'] = (
                'Нужно проверить базу'
            )
            item['recommendation'] = (
                'Недостаточно данных по темам: '
                + ', '.join(item['uncertain_dependencies'])
                + '. Пройди по ним диагностику.'
            )

        elif item['priority'] == 'high':
            item['status_label'] = (
                'Изучить в первую очередь'
            )
            item['recommendation'] = (
                'Повтори теорию и реши дополнительные задания.'
            )

        elif item['priority'] == 'medium':
            item['status_label'] = (
                'Закрепить знания'
            )
            item['recommendation'] = (
                'Повтори основные правила и закрепи знания практикой.'
            )

        elif item['priority'] == 'low':
            item['status_label'] = (
                'Поддерживать уровень'
            )
            item['recommendation'] = (
                'Продолжай решать задания для сохранения результата.'
            )

        else:
            item['status_label'] = (
                'Нужно больше данных'
            )
            item['recommendation'] = (
                'Пройди дополнительные задания для оценки знаний.'
            )

    return ordered_roadmap

