# Al-Kabry — Платформа для сравнительного анализа алгоритмов рекомендаций в электронной коммерции

[![Django](https://img.shields.io/badge/Django-5.0.4-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4.1-orange.svg)](https://scikit-learn.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)](https://getbootstrap.com/)

Полноценная электронная торговая платформа на Django, разработанная для сравнительного анализа пяти алгоритмов рекомендаций на воспроизводимом наборе данных о товарах моды (120 товаров, 500 пользователей, более 6 000 взаимодействий, источник — Kaggle).

---

## Содержание

- [Описание проекта](#описание-проекта)
- [Алгоритмы рекомендаций](#алгоритмы-рекомендаций)
- [Технологический стек](#технологический-стек)
- [Системные требования](#системные-требования)
- [Быстрый старт](#быстрый-старт)
- [Подробная установка](#подробная-установка)
- [Настройка PostgreSQL](#настройка-postgresql)
- [Команды управления](#команды-управления)
- [Учётные данные](#учётные-данные)
- [Структура проекта](#структура-проекта)
- [Результаты оценки алгоритмов](#результаты-оценки-алгоритмов)
- [Jupyter-ноутбуки](#jupyter-ноутбуки)
- [Переменные окружения](#переменные-окружения)
- [Развёртывание](#развёртывание)
- [Устранение неполадок](#устранение-неполадок)

---

## Описание проекта

Проект представляет собой исследовательскую платформу, сочетающую функциональный интернет-магазин с встроенным стендом для оценки алгоритмов рекомендаций. Все алгоритмы реализованы с нуля на базе библиотеки scikit-learn без использования специализированных фреймворков рекомендательных систем, что обеспечивает прозрачность и воспроизводимость экспериментов.

### Функциональность платформы

- Каталог товаров с иерархическими категориями и фильтрацией по атрибутам
- Корзина покупок с динамическими обновлениями через HTMX без перезагрузки страницы
- Аутентификация пользователей, личный кабинет и история заказов
- Система отзывов и рейтингов товаров
- Полный цикл оформления заказа с контролем остатков
- Живой поиск с задержкой 300 мс
- Многоязычный чат-ассистент (EN, ES, RU, AR)
- Адаптивный интерфейс на Bootstrap 5

### Система рекомендаций

- Пять независимых алгоритмов рекомендаций, реализованных средствами scikit-learn
- Персонализированные рекомендации в реальном времени на главной странице и карточке товара
- Отслеживание событий взаимодействия: просмотр, клик, добавление в корзину, покупка, отзыв
- Полный набор метрик качества: Precision@10, Recall@10, NDCG@10, MRR, Hit Rate, F1, Diversity, Coverage
- Трёхкратная перекрёстная проверка (сиды: 2026, 2027, 2028) для статистически устойчивых результатов

### Аналитика и сравнение

- Панель мониторинга производительности алгоритмов с визуализацией через Chart.js
- Сравнение алгоритмов в режиме реального времени с историческим трекингом
- Отслеживание CTR и коэффициента конверсии
- Автоматическая генерация рейтинговых отчётов

---

## Алгоритмы рекомендаций

| N | Алгоритм | Подход | Вес в гибриде |
|---|----------|--------|---------------|
| 1 | Контентная фильтрация | TF-IDF + косинусное сходство по признакам товара | 10% |
| 2 | Коллаборативная (по пользователям) | Матрица сходства пользователей; товары, понравившиеся похожим пользователям | 35% |
| 3 | Коллаборативная (по товарам) | Матрица сходства товаров; похожие позиции | 40% |
| 4 | SVD (матричная факторизация) | TruncatedSVD; скрытые факторы пользователь-товар | 15% |
| 5 | Гибридная система | Взвешенный ансамбль четырёх алгоритмов выше | — |

Формула итоговой точности, применяемая для ранжирования алгоритмов:

```
Accuracy = Hit Rate * 0.50 + NDCG * 0.30 + Precision * 0.20
```

---

## Технологический стек

| Уровень | Технология |
|---------|-----------|
| Бэкенд | Django 5.0.4 |
| База данных | SQLite (разработка) / PostgreSQL 14+ (продакшн) |
| Фронтенд | Django Templates, Bootstrap 5.3 |
| Динамический интерфейс | HTMX 1.9.10 |
| Визуализация | Chart.js 4.4.0 |
| ML-библиотеки | scikit-learn 1.4, numpy 1.26, pandas 2.2, scipy 1.12 |
| Формы | django-crispy-forms, crispy-bootstrap5 |
| Фильтрация | django-filter |
| Аналитические ноутбуки | Jupyter, matplotlib |

---

## Системные требования

- Python 3.12 и выше
- pip
- PostgreSQL 14+ (опционально; по умолчанию используется SQLite)
- Набор данных Kaggle `styles.csv` (необходим для генерации бенчмарк-данных)

---

## Быстрый старт

```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 2. Применить миграции
python manage.py migrate

# 3. Сгенерировать бенчмарк-данные (необходим CSV-файл Kaggle, см. ниже)
python manage.py generate_benchmark_data

# 4. Запустить сервер разработки
python manage.py runserver
```

Открыть в браузере: http://localhost:8000

---

## Подробная установка

### 1. Клонирование репозитория и установка зависимостей

```bash
git clone https://github.com/abdelgukhari/kabbary_store_main.git
cd Al-kabry

python -m venv venv

# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

Устанавливаемые пакеты: Django 5.0.4, Pillow, crispy-bootstrap5, django-crispy-forms, django-filter, django-htmx, numpy, pandas, scipy, scikit-learn, python-decouple, psycopg2-binary.

### 2. Настройка окружения

```bash
cp .env.example .env
# Отредактировать .env согласно разделу «Переменные окружения»
```

### 3. Применение миграций

```bash
python manage.py migrate
```

### 4. Генерация бенчмарк-данных

Команда импортирует реальные товары из CSV-файла Kaggle и запускает оценку всех пяти алгоритмов методом трёхкратной перекрёстной проверки.

**Получение набора данных.** Скачайте `styles.csv` из набора данных [Fashion Product Images Small](https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-small) на Kaggle и поместите файл по пути:

```
data/fashion-product-images-small/styles.csv
```

**Запуск генерации:**

```bash
# По умолчанию: 120 товаров, 500 пользователей, 8 подкатегорий, 5% шума
python manage.py generate_benchmark_data

# Указать путь к CSV вручную
python manage.py generate_benchmark_data --csv-file path/to/styles.csv

# Изменить долю случайных взаимодействий
python manage.py generate_benchmark_data --noise-pct 0.10
```

| Флаг | Описание | Значение по умолчанию |
|------|----------|-----------------------|
| `--csv-file` | Путь к файлу `styles.csv` | `data/fashion-product-images-small/styles.csv` |
| `--noise-pct` | Доля «шумовых» взаимодействий | `0.05` |

В результате создаются:
- 120 товаров в 8 подкатегориях моды (по 15 в каждой): Topwear, Bottomwear, Shoes, Sandal, Bags, Watches, Jewellery, Fragrance
- 500 пользователей со структурированными профилями предпочтений
- более 6 000 взаимодействий (предпочтения + шум)
- записи `AlgorithmMetrics` для всех пяти алгоритмов

Время генерации: 60–120 секунд в зависимости от аппаратного обеспечения.

**Альтернатива — синтетический набор данных (CSV не требуется):**

```bash
python manage.py generate_dataset --clear --users 150
```

### 5. Запуск сервера разработки

```bash
python manage.py runserver
```

---

## Настройка PostgreSQL

### Linux / macOS (автоматический скрипт)

```bash
chmod +x setup_postgres.sh
./setup_postgres.sh
```

Скрипт создаёт базу данных `ecommerce_alkabry`, пользователя `ecommerce_user` с паролем `ecommerce_pass_2026`.

### Ручная настройка (Windows и другие ОС)

```sql
CREATE DATABASE ecommerce_alkabry;
CREATE USER ecommerce_user WITH PASSWORD 'ecommerce_pass_2026';
GRANT ALL PRIVILEGES ON DATABASE ecommerce_alkabry TO ecommerce_user;
```

### Настройка файла `.env`

```env
DB_ENGINE=postgresql
DB_NAME=ecommerce_alkabry
DB_USER=ecommerce_user
DB_PASSWORD=ecommerce_pass_2026
DB_HOST=localhost
DB_PORT=5432
```

После этого:

```bash
python manage.py migrate
python manage.py generate_benchmark_data
```

---

## Команды управления

### Генерация и оценка данных

```bash
# Основная команда бенчмарка (120 товаров, 500 пользователей, требуется CSV)
python manage.py generate_benchmark_data

# Синтетический набор данных (CSV не нужен)
python manage.py generate_dataset --clear --users 150

# Сравнение алгоритмов методом трёхкратной перекрёстной проверки
python manage.py compare_algorithms

# Повторное обучение моделей (сброс кеша, перестройка матриц)
python manage.py retrain_recommendation_models

# Обновление кеша аналитических метрик
python manage.py cache_algorithm_metrics
```

### База данных

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py dumpdata --natural-foreign --natural-primary \
    -e contenttypes -e auth.Permission --indent 2 > backup.json
python manage.py loaddata backup.json
```

### Статические файлы

```bash
python manage.py collectstatic --noinput
python manage.py collectstatic --clear --noinput
```

---

## Учётные данные

### Учётная запись администратора (создаётся командой `generate_benchmark_data`)

```
Email:    admin@alkabry.com
Пароль:   admin123
URL:      http://localhost:8000/admin/
```

### Бенчмарк-пользователи (500 аккаунтов)

```
Email:    pruser001@perfectreal.test  ...  pruser500@perfectreal.test
Пароль:   testpass2026!
```

---

## Структура проекта

```
Al-kabry/
├── config/                          # Настройки Django-проекта и маршрутизация
│   ├── settings.py
│   └── urls.py
│
├── accounts/                        # Аутентификация, профили, личный кабинет
├── products/                        # Каталог товаров, поиск, фильтрация
│   └── management/commands/
│       ├── generate_benchmark_data.py   # Основная команда генерации данных
│       ├── generate_dataset.py          # Синтетические данные (без CSV)
│       └── compare_algorithms.py        # Оценка методом кросс-валидации
│
├── cart/                            # Корзина покупок (сессия + БД)
├── orders/                          # Оформление и управление заказами
│
├── recommendations/                 # Движок рекомендаций
│   ├── services.py                  # Все пять алгоритмов и гибридная система
│   ├── models.py                    # UserInteraction, RecommendationEvent
│   └── management/commands/
│       └── retrain_recommendation_models.py
│
├── analytics/                       # Панель мониторинга и отчёты
│   ├── models.py                    # AlgorithmMetrics, ComparisonReport
│   └── management/commands/
│       └── cache_algorithm_metrics.py
│
├── chatbot/                         # Чат-ассистент с NLP-парсингом
│   └── i18n.py                      # Переводы (EN, ES, RU, AR)
│
├── templates/                       # HTML-шаблоны Django
├── static/                          # Исходные CSS и JS
├── media/                           # Загружаемые пользователями файлы
│
├── data/
│   └── fashion-product-images-small/
│       └── styles.csv               # Набор данных Kaggle (поместить сюда)
│
├── notebook.ipynb                   # Основной аналитический ноутбук
├── comparison_results.ipynb         # Результаты сравнения алгоритмов
├── recommendation_evaluation.ipynb  # Детальный анализ метрик оценки
├── thesis_colab (1).ipynb           # Версия для Google Colab
│
├── manage.py
├── requirements.txt
├── .env                             # Локальные переменные окружения (в .gitignore)
├── .env.example                     # Шаблон для .env
└── db.sqlite3                       # База данных SQLite (разработка)
```

---

## Результаты оценки алгоритмов

Оценка проводится методом трёхкратной перекрёстной проверки (сиды: 2026, 2027, 2028), k = 10 рекомендаций.

| Алгоритм | Вес в гибридной системе |
|----------|------------------------|
| Item-Based CF | 40% |
| User-Based CF | 35% |
| SVD | 15% |
| Контентная фильтрация | 10% |

Гибридная система превосходит каждый отдельный алгоритм, поскольку в итоговый список включаются только товары, получившие высокую оценку сразу от нескольких методов, что повышает точность и устойчивость рекомендаций.

Подробные результаты доступны на панели мониторинга `/analytics/` (требуется вход под учётной записью персонала) или через команду:

```bash
python manage.py compare_algorithms
```

---

## Jupyter-ноутбуки

| Ноутбук | Назначение |
|---------|-----------|
| `notebook.ipynb` | Разведочный анализ данных и разработка алгоритмов |
| `comparison_results.ipynb` | Метрики и визуализация сравнения алгоритмов |
| `recommendation_evaluation.ipynb` | Детальный анализ метрик, кросс-валидация |
| `thesis_colab (1).ipynb` | Версия для Google Colab (вычислительные эксперименты) |

Запуск ноутбуков:

```bash
pip install jupyter
jupyter notebook
```

---

## Переменные окружения

Содержимое файла `.env`:

```env
SECRET_KEY=ваш-секретный-ключ
DEBUG=True
ALLOWED_HOSTS=*

# База данных (по умолчанию SQLite)
DB_ENGINE=sqlite

# Только при DB_ENGINE=postgresql
DB_NAME=ecommerce_alkabry
DB_USER=ecommerce_user
DB_PASSWORD=ecommerce_pass_2026
DB_HOST=localhost
DB_PORT=5432
```

---

## Развёртывание

Контрольный список для перехода в продакшн:

1. Установить `DEBUG=False` и задать надёжный `SECRET_KEY` в `.env`.
2. Перейти на PostgreSQL.
3. Собрать статические файлы: `python manage.py collectstatic --noinput`.
4. Запустить через gunicorn: `gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3`.
5. Настроить nginx как обратный прокси для раздачи `/static/` и `/media/`.

---

## Устранение неполадок

**Порт уже занят**

```bash
# Linux / macOS
lsof -ti:8000 | xargs kill -9

# Запуск на другом порту
python manage.py runserver 8080
```

**CSV-файл Kaggle не найден**

```
FileNotFoundError: Kaggle CSV not found at: data/fashion-product-images-small/styles.csv
```

Скачайте `styles.csv` с Kaggle и поместите его по указанному пути, либо передайте путь явно: `--csv-file <путь>`.

**Ошибки миграций (только для разработки)**

```bash
# Полный сброс — только для разработки!
rm -rf */migrations/0*.py
rm db.sqlite3
python manage.py makemigrations
python manage.py migrate
```

**Статические файлы не загружаются**

```bash
python manage.py collectstatic --clear --noinput
```

**Ошибка Module Not Found**

```bash
pip install -r requirements.txt --force-reinstall
```

---

Проект разработан в рамках дипломной работы для сравнительного исследования алгоритмов рекомендаций в контексте электронной коммерции.
#   A l K a b r y  
 #   A l K a b r y  
 