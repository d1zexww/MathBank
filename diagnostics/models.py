
from django.db import models
from django.conf import settings


# Банк диагностических заданий
class DiagnosticQuestion(models.Model):

    SUBJECT_CHOICES = [
        ('profile_math', 'Профильная математика'),
        ('russian', 'Русский язык'),
        ('english', 'Английский язык'),
        ('informatics', 'Информатика'),
    ]

    DIFFICULTY_CHOICES = [
        ('easy', 'Лёгкий'),
        ('medium', 'Средний'),
        ('hard', 'Сложный'),
    ]

    # Основная информация о задании
    subject = models.CharField(
        max_length=30,
        choices=SUBJECT_CHOICES
    )

    topic = models.CharField(
        max_length=120
    )

    ege_task_number = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name='Номер задания ЕГЭ'
    )

    question_text = models.TextField(
        verbose_name='Условие задания'
    )

    # Изображение: чертёж, схема или рисунок
    image = models.ImageField(
        upload_to='diagnostics/questions/',
        blank=True,
        null=True,
        verbose_name='Изображение задания'
    )

    # Правильный ответ и объяснение
    correct_answer = models.CharField(
        max_length=255
    )

    explanation = models.TextField(
        blank=True
    )

    # Сложность задания
    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default='medium'
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f'{self.topic} — {self.get_subject_display()}'

    class Meta:
        verbose_name = 'Диагностическое задание'
        verbose_name_plural = 'Диагностические задания'


# Попытка прохождения диагностики
class DiagnosticAttempt(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='diagnostic_attempts'
    )

    subject = models.CharField(
        max_length=30
    )

    started_at = models.DateTimeField(
        auto_now_add=True
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    score = models.PositiveSmallIntegerField(
        default=0
    )

    total_questions = models.PositiveSmallIntegerField(
        default=0
    )

    is_completed = models.BooleanField(
        default=False
    )

    def __str__(self):
        return f'{self.user.username} — {self.subject}'

    class Meta:
        verbose_name = 'Попытка диагностики'
        verbose_name_plural = 'Попытки диагностики'


# Ответы учеников
class DiagnosticAnswer(models.Model):

    attempt = models.ForeignKey(
        DiagnosticAttempt,
        on_delete=models.CASCADE,
        related_name='answers'
    )

    question = models.ForeignKey(
        DiagnosticQuestion,
        on_delete=models.CASCADE,
        related_name='student_answers'
    )

    user_answer = models.CharField(
        max_length=255,
        blank=True
    )

    is_correct = models.BooleanField(
        default=False
    )

    answered_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['attempt', 'question'],
                name='unique_question_per_diagnostic_attempt'
            )
        ]

        verbose_name = 'Ответ ученика'
        verbose_name_plural = 'Ответы учеников'

    def __str__(self):
        return f'Ответ: {self.question.topic}'
