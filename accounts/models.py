from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class StudentProfile(models.Model):

    SUBJECT_CHOICES = [
        ('profile_math', 'Профильная математика'),
        ('russian', 'Русский язык'),
        ('english', 'Английский язык'),
        ('informatics', 'Информатика'),
        ('physics', 'Физика'),
        ('biology', 'Биология'),
        ('chemistry', 'Химия'),
        ('history', 'История'),
        ('social_studies', 'Обществознание'),
        ('literature', 'Литература'),
        ('geography', 'География'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )

    full_name = models.CharField(
        max_length=100,
        blank=True
    )

    main_subject = models.CharField(
        max_length=30,
        choices=SUBJECT_CHOICES,
        blank=True
    )

    target_score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(100)
        ]
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Профиль {self.user.username}'