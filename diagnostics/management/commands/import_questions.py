
import csv
from pathlib import Path

from PIL import Image

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError

from diagnostics.models import DiagnosticQuestion


class Command(BaseCommand):

    help = 'Массовый импорт диагностических заданий из CSV'

    def add_arguments(self, parser):

        parser.add_argument(
            'csv_file',
            type=str,
            help='Путь к CSV-файлу с заданиями'
        )

        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Проверить файл без сохранения заданий'
        )

    def handle(self, *args, **options):

        csv_path = Path(
            options['csv_file']
        ).expanduser().resolve()

        dry_run = options['dry_run']

        if not csv_path.is_file():
            raise CommandError(
                f'CSV-файл не найден: {csv_path}'
            )

        subjects = {
            value
            for value, label
            in DiagnosticQuestion.SUBJECT_CHOICES
        }

        difficulties = {
            value
            for value, label
            in DiagnosticQuestion.DIFFICULTY_CHOICES
        }

        required_columns = {
            'subject',
            'topic',
            'question_text',
            'correct_answer',
        }

        created = 0
        duplicates = 0
        errors = 0
        checked = 0

        # Открываем CSV
        with csv_path.open(
            'r',
            encoding='utf-8-sig',
            newline=''
        ) as csv_file:

            sample = csv_file.read(4096)
            csv_file.seek(0)

            try:
                dialect = csv.Sniffer().sniff(
                    sample,
                    delimiters=',;\t'
                )
                delimiter = dialect.delimiter

            except csv.Error:
                delimiter = ';'

            reader = csv.DictReader(
                csv_file,
                delimiter=delimiter
            )

            if not reader.fieldnames:
                raise CommandError('CSV-файл пустой.')

            reader.fieldnames = [
                name.strip()
                for name in reader.fieldnames
            ]

            missing = required_columns - set(reader.fieldnames)

            if missing:
                raise CommandError(
                    'Отсутствуют колонки: '
                    + ', '.join(sorted(missing))
                )

            # Обрабатываем задания
            for row_number, row in enumerate(reader, start=2):

                try:

                    subject = (
                        row.get('subject') or ''
                    ).strip()

                    topic = (
                        row.get('topic') or ''
                    ).strip()

                    question_text = (
                        row.get('question_text') or ''
                    ).strip()

                    correct_answer = (
                        row.get('correct_answer') or ''
                    ).strip()

                    explanation = (
                        row.get('explanation') or ''
                    ).strip()

                    difficulty = (
                        row.get('difficulty') or 'medium'
                    ).strip()

                    image_value = (
                        row.get('image') or ''
                    ).strip()

                    number_value = (
                        row.get('ege_task_number') or ''
                    ).strip()

                    active_value = (
                        row.get('is_active') or 'true'
                    ).strip().lower()

                    # Обязательные поля
                    if not subject or not topic:
                        raise ValueError(
                            'Не указан предмет или тема.'
                        )

                    if not question_text or not correct_answer:
                        raise ValueError(
                            'Не указано условие или правильный ответ.'
                        )

                    # Проверяем предмет
                    if subject not in subjects:
                        raise ValueError(
                            f'Неизвестный предмет: {subject}'
                        )

                    # Проверяем сложность
                    if difficulty not in difficulties:
                        raise ValueError(
                            f'Неизвестная сложность: {difficulty}'
                        )

                    # Проверяем номер ЕГЭ
                    ege_number = None

                    if number_value:
                        ege_number = int(number_value)

                        if ege_number < 1:
                            raise ValueError(
                                'Номер ЕГЭ должен быть положительным.'
                            )

                    # Проверяем активность
                    if active_value in (
                        'true', '1', 'yes', 'да'
                    ):
                        is_active = True

                    elif active_value in (
                        'false', '0', 'no', 'нет'
                    ):
                        is_active = False

                    else:
                        raise ValueError(
                            'Некорректное значение is_active.'
                        )

                    # Проверяем изображение
                    image_path = None

                    if image_value:

                        image_path = Path(image_value)

                        if not image_path.is_absolute():
                            image_path = csv_path.parent / image_path

                        image_path = image_path.resolve()

                        if not image_path.is_file():
                            raise ValueError(
                                f'Изображение не найдено: {image_path}'
                            )

                        with Image.open(image_path) as img:
                            img.verify()

                    # Проверяем дубликаты
                    duplicate = DiagnosticQuestion.objects.filter(
                        subject=subject,
                        topic=topic,
                        question_text=question_text,
                        ege_task_number=ege_number,
                    ).exists()

                    if duplicate:

                        duplicates += 1

                        self.stdout.write(
                            self.style.WARNING(
                                f'Строка {row_number}: '
                                'дубликат пропущен.'
                            )
                        )

                        continue

                    checked += 1

                    # Только проверка без сохранения
                    if dry_run:

                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Строка {row_number}: '
                                'проверка успешна.'
                            )
                        )

                        continue

                    # Создаём объект задания
                    question = DiagnosticQuestion(
                        subject=subject,
                        topic=topic,
                        ege_task_number=ege_number,
                        question_text=question_text,
                        correct_answer=correct_answer,
                        explanation=explanation,
                        difficulty=difficulty,
                        is_active=is_active,
                    )

                    # Прикрепляем изображение
                    if image_path:

                        with image_path.open('rb') as img:
                            question.image.save(
                                image_path.name,
                                File(img),
                                save=False
                            )

                    # Сохраняем в базу данных
                    question.save()

                    created += 1

                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Строка {row_number}: '
                            f'добавлено — {topic}.'
                        )
                    )

                except Exception as exc:

                    errors += 1

                    self.stdout.write(
                        self.style.ERROR(
                            f'Строка {row_number}: {exc}'
                        )
                    )

        # Итоговый отчёт
        self.stdout.write('')
        self.stdout.write(
            '========== ИТОГ ИМПОРТА =========='
        )

        self.stdout.write(f'Проверено: {checked}')
        self.stdout.write(f'Добавлено: {created}')
        self.stdout.write(f'Дубликатов: {duplicates}')
        self.stdout.write(f'Ошибок: {errors}')

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    'Режим проверки: база данных не изменялась.'
                )
            )
