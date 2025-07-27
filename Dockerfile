#  Используем Python 3.11
FROM python:3.11

# Устанавливаем переменные окружения для правильного поведения Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Рабочая директория
WORKDIR /app

# Копируем зависимости и устанавливаем
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install gunicorn

#  Копируем проект целиком
COPY . .

#  Открываем порт (на всякий случай)
EXPOSE 8000

#  Стартуем Gunicorn (это работает только если не будет перекрыто в docker-compose)
CMD ["gunicorn", "sitecinema.wsgi:application", "--bind", "0.0.0.0:8000"]