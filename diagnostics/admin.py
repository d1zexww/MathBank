from django.contrib import admin
from .models import (
    DiagnosticQuestion,
    DiagnosticAttempt,
    DiagnosticAnswer
)


# Администрирование диагностических заданий
@admin.register(DiagnosticQuestion)
class DiagnosticQuestionAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'topic',
        'subject',
        'ege_task_number',
        'difficulty',
        'is_active',
        'created_at',
    )

    list_filter = (
        'subject',
        'difficulty',
        'is_active',
    )

    search_fields = (
        'topic',
        'question_text',
    )


# Администрирование попыток диагностики
@admin.register(DiagnosticAttempt)
class DiagnosticAttemptAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'user',
        'subject',
        'score',
        'total_questions',
        'is_completed',
        'started_at',
    )

    list_filter = (
        'subject',
        'is_completed',
    )

    search_fields = (
        'user__username',
        'subject',
    )


# Администрирование ответов учеников
@admin.register(DiagnosticAnswer)
class DiagnosticAnswerAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'attempt',
        'question',
        'user_answer',
        'is_correct',
        'answered_at',
    )

    list_filter = (
        'is_correct',
    )

    search_fields = (
        'question__topic',
        'attempt__user__username',
    )