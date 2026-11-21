from .roadmap import build_roadmap
import random

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction

from .models import (
    DiagnosticQuestion,
    DiagnosticAttempt,
    DiagnosticAnswer,
)


# =========================================
# НОРМАЛИЗАЦИЯ ОТВЕТОВ
# =========================================

def normalize_answer(value):
    return (
        (value or '')
        .strip()
        .replace('−', '-')
        .casefold()
    )


# =========================================
# НАЧАЛО ДИАГНОСТИКИ
# =========================================

@login_required
def start_diagnostic(request):

    active_questions = DiagnosticQuestion.objects.filter(
        is_active=True
    )

    available_subjects = list(
        active_questions
        .values_list('subject', flat=True)
        .distinct()
    )

    topic_options = list(
        active_questions
        .values_list('subject', 'topic')
        .distinct()
        .order_by('subject', 'topic')
    )

    task_numbers = list(
        active_questions
        .exclude(ege_task_number__isnull=True)
        .values_list('ege_task_number', flat=True)
        .distinct()
        .order_by('ege_task_number')
    )

    error = None

    selected_subject = ''
    selected_topic = ''
    selected_task_number = ''
    selected_question_count = '10'

    if request.method == 'POST':

        selected_subject = request.POST.get(
            'subject', ''
        ).strip()

        selected_topic = request.POST.get(
            'topic', ''
        ).strip()

        selected_task_number = request.POST.get(
            'ege_task_number', ''
        ).strip()

        selected_question_count = request.POST.get(
            'question_count', '10'
        ).strip()

        valid_counts = {'5', '10', '12', '15', '20'}

        if selected_subject not in available_subjects:
            error = 'Выберите корректный предмет.'

        elif selected_question_count not in valid_counts:
            error = 'Выберите корректное количество вопросов.'

        else:

            questions_query = active_questions.filter(
                subject=selected_subject
            )

            # Фильтр по теме
            if selected_topic:
                questions_query = questions_query.filter(
                    topic=selected_topic
                )

            # Фильтр по номеру задания
            if selected_task_number:

                try:
                    task_number = int(selected_task_number)

                    questions_query = questions_query.filter(
                        ege_task_number=task_number
                    )

                except ValueError:
                    error = 'Некорректный номер задания.'

            # Временное разделение задания №7
            if (
                selected_subject == 'profile_math'
                and selected_task_number == '7'
            ):
                questions_query = questions_query.filter(
                    id__gte=19,
                    id__lte=30
                )

            if not error:

                questions = list(questions_query)

                if not questions:
                    error = 'По выбранным параметрам вопросов нет.'

                else:

                    question_count = int(
                        selected_question_count
                    )

                    if question_count > len(questions):

                        error = (
                            f'Доступно только {len(questions)} вопросов. '
                            f'Выберите меньшее количество.'
                        )

                    else:

                        selected_questions = random.sample(
                            questions,
                            question_count
                        )

                        with transaction.atomic():

                            attempt = DiagnosticAttempt.objects.create(
                                user=request.user,
                                subject=selected_subject,
                                total_questions=len(selected_questions)
                            )

                            DiagnosticAnswer.objects.bulk_create([
                                DiagnosticAnswer(
                                    attempt=attempt,
                                    question=question
                                )
                                for question in selected_questions
                            ])

                        return redirect(
                            'diagnostics:take',
                            attempt_id=attempt.id
                        )

    context = {
        'subjects': available_subjects,
        'topic_options': topic_options,
        'task_numbers': task_numbers,
        'error': error,
        'selected_subject': selected_subject,
        'selected_topic': selected_topic,
        'selected_task_number': selected_task_number,
        'selected_question_count': selected_question_count,
    }

    return render(
        request,
        'diagnostics/start.html',
        context
    )


# =========================================
# ПРОХОЖДЕНИЕ ДИАГНОСТИКИ
# =========================================

@login_required
def take_diagnostic(request, attempt_id):

    attempt = get_object_or_404(
        DiagnosticAttempt,
        id=attempt_id,
        user=request.user,
        is_completed=False
    )

    answers = (
        attempt.answers
        .select_related('question')
        .all()
    )

    if request.method == 'POST':

        for answer in answers:

            user_answer = request.POST.get(
                f'question_{answer.question.id}',
                ''
            )

            answer.user_answer = user_answer

            normalized_user_answer = normalize_answer(
                user_answer
            )

            normalized_correct_answer = normalize_answer(
                answer.question.correct_answer
            )

            answer.is_correct = (
                bool(normalized_user_answer)
                and normalized_user_answer == normalized_correct_answer
            )

            answer.save()

        correct_count = answers.filter(
            is_correct=True
        ).count()

        attempt.score = correct_count
        attempt.is_completed = True
        attempt.completed_at = timezone.now()
        attempt.save()

        return redirect(
            'diagnostics:result',
            attempt_id=attempt.id
        )

    return render(
        request,
        'diagnostics/take.html',
        {
            'attempt': attempt,
            'answers': answers,
        }
    )


# =========================================
# РЕЗУЛЬТАТЫ И АНАЛИТИКА
# =========================================

@login_required
def diagnostic_result(request, attempt_id):

    attempt = get_object_or_404(
        DiagnosticAttempt,
        id=attempt_id,
        user=request.user,
        is_completed=True
    )

    answers = list(
        attempt.answers
        .select_related('question')
        .all()
    )

    percentage = 0

    if attempt.total_questions:
        percentage = round(
            attempt.score / attempt.total_questions * 100
        )

    correct_count = 0
    wrong_count = 0
    skipped_count = 0

    topic_statistics = {}

    for answer in answers:

        user_answer = normalize_answer(
            answer.user_answer
        )

        topic = answer.question.topic or 'Без темы'

        if topic not in topic_statistics:
            topic_statistics[topic] = {
                'topic': topic,
                'total': 0,
                'correct': 0,
                'wrong': 0,
                'skipped': 0,
            }

        topic_statistics[topic]['total'] += 1

        if not user_answer:

            skipped_count += 1
            topic_statistics[topic]['skipped'] += 1

        elif answer.is_correct:

            correct_count += 1
            topic_statistics[topic]['correct'] += 1

        else:

            wrong_count += 1
            topic_statistics[topic]['wrong'] += 1

    # Процент правильных ответов по каждой теме
    topic_statistics_list = []

    for topic_data in topic_statistics.values():

        if topic_data['total']:
            topic_data['percentage'] = round(
                topic_data['correct'] / topic_data['total'] * 100
            )
        else:
            topic_data['percentage'] = 0

        topic_statistics_list.append(topic_data)

    # Сначала темы с худшими результатами
    topic_statistics_list.sort(
        key=lambda item: item['percentage']
    )

    subject_labels = dict(
        DiagnosticQuestion.SUBJECT_CHOICES
    )

    subject_name = subject_labels.get(
        attempt.subject,
        attempt.subject
    )

    context = {
        'attempt': attempt,
        'answers': answers,
        'percentage': percentage,

        'subject_name': subject_name,
        'subject_label': subject_name,

        'correct_count': correct_count,
        'wrong_count': wrong_count,
        'skipped_count': skipped_count,

        'topic_statistics': topic_statistics_list,
    }

    return render(
        request,
        'diagnostics/result.html',
        context
    )


# =========================================
# ИСТОРИЯ ДИАГНОСТИК
# =========================================

@login_required

@login_required
def diagnostic_history(request):

    subject_labels = dict(
        DiagnosticQuestion.SUBJECT_CHOICES
    )

    # Все завершённые диагностики пользователя
    all_attempts = (
        DiagnosticAttempt.objects
        .filter(
            user=request.user,
            is_completed=True
        )
        .order_by('-completed_at')
    )

    # Выбранный предмет
    selected_subject = request.GET.get(
        'subject', ''
    ).strip()

    # Проверяем корректность фильтра
    if selected_subject not in subject_labels:
        selected_subject = ''

    # Применяем фильтр
    if selected_subject:
        attempts = all_attempts.filter(
            subject=selected_subject
        )
    else:
        attempts = all_attempts

    history_items = []
    percentages = []

    for attempt in attempts:

        percentage = 0

        if attempt.total_questions:
            percentage = round(
                attempt.score / attempt.total_questions * 100
            )

        percentages.append(percentage)

        history_items.append({
            'attempt': attempt,
            'percentage': percentage,
            'subject_name': subject_labels.get(
                attempt.subject,
                attempt.subject
            ),
        })

    # Статистика
    total_attempts = len(history_items)

    average_score = 0
    best_score = 0

    if percentages:

        average_score = round(
            sum(percentages) / len(percentages)
        )

        best_score = max(percentages)

    # Данные для графика: от старых попыток к новым
    chart_items = list(reversed(history_items))

    context = {
        'history_items': history_items,
        'chart_items': chart_items,

        'total_attempts': total_attempts,
        'average_percentage': average_score,
        'best_percentage': best_score,

        'subjects': DiagnosticQuestion.SUBJECT_CHOICES,
        'selected_subject': selected_subject,

        'active_page': 'history',
    }

    return render(
        request,
        'diagnostics/history.html',
        context
    )
@login_required
def roadmap_view(request):
    roadmap = build_roadmap(request.user)

    high_priority = [
        item for item in roadmap
        if item['priority'] == 'high'
    ]

    medium_priority = [
        item for item in roadmap
        if item['priority'] == 'medium'
    ]

    low_priority = [
        item for item in roadmap
        if item['priority'] == 'low'
    ]

    insufficient_data = [
        item for item in roadmap
        if item['priority'] == 'insufficient_data'
    ]

    return render(
        request,
        'diagnostics/roadmap.html',
        {
            'roadmap': roadmap,
            'high_priority': high_priority,
            'medium_priority': medium_priority,
            'low_priority': low_priority,
            'insufficient_data': insufficient_data,
            'total_topics': len(roadmap),
        }
    )


