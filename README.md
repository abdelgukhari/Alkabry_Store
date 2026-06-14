# Al-Kabry — Платформа для сравнительного анализа алгоритмов рекомендаций в электронной коммерции

[![Django](https://img.shields.io/badge/Django-5.0.4-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4.1-orange.svg)](https://scikit-learn.org/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)](https://getbootstrap.com/)

Полноценная электронная торговая платформа на Django, разработанная для сравнительного анализа пяти алгоритмов рекомендаций на воспроизводимом наборе данных о товарах моды. Основная команда для генерации данных и оценки алгоритмов — `generate_benchmark_data`.

---

## Содержание

- [Описание проекта](#описание-проекта)
- [Алгоритмы рекомендаций](#алгоритмы-рекомендаций)
- [Технологический стек](#технологический-стек)
- [Системные требования](#системные-требования)
- [Быстрый старт](#быстрый-старт)
- [Подробная установка](#подробная-установка)
- [Команда generate_benchmark_data](#команда-generate_benchmark_data)
- [Остальные команды управления](#остальные-команды-управления)
- [Учётные данные](#учётные-данные)
- [Структура проекта](#структура-проекта)
- [Результаты оценки алгоритмов](#результаты-оценки-алгоритмов)
- [Jupyter-ноутбук](#jupyter-ноутбук)
- [Переменные окружения](#переменные-окружения)
- [Развёртывание](#развёртывание)
- [Устранение неполадок](#устранение-неполадок)

---

## Описание проекта

Проект представляет собой исследовательскую платформу, сочетающую интернет-магазин с встроенным стендом для оценки алгоритмов рекомендаций. Все алгоритмы реализованы с нуля на базе библиотеки scikit-learn.

### Функциональность платформы

- Каталог товаров с иерархическими категориями и фильтрацией
- Корзина покупок с динамическими обновлениями через HTMX
- Аутентификация пользователей, личный кабинет, история заказов
- Система отзывов и рейтингов
- Полный цикл оформления заказа
- Живой поиск с задержкой 300 мс
- Многоязычный чат-ассистент (EN, ES, RU, AR)
- Адаптивный интерфейс на Bootstrap 5

### Система рекомендаций

- Пять независимых алгоритмов рекомендаций
- Персонализированные рекомендации в реальном времени
- Отслеживание событий: просмотр, клик, добавление в корзину, покупка, отзыв
- Метрики качества: Precision@10, Recall@10, NDCG@10, MRR, Hit Rate, F1
- Трёхкратная перекрёстная проверка (сиды: 2026, 2027, 2028)

---

## Алгоритмы рекомендаций

| N | Алгоритм | Подход | Вес в гибриде |
|---|----------|--------|---------------|
| 1 | Коллаборативная (по товарам) | Матрица сходства товаров | 40% |
| 2 | Коллаборативная (по пользователям) | Матрица сходства пользователей | 35% |
| 3 | SVD | TruncatedSVD, скрытые факторы | 15% |
| 4 | Контентная фильтрация | TF-IDF + косинусное сходство по признакам товара | 10% |
| 5 | Гибридная система | Взвешенный ансамбль четырёх алгоритмов | — |

Формула итоговой точности:

```
Accuracy = Hit Rate * 0.50 + NDCG * 0.30 + Precision * 0.20
```

---

## Технологический стек

| Уровень | Технология |
|---------|-----------|
| Бэкенд | Django 5.0.4 |
| База данных | SQLite / PostgreSQL 14+ |
| Фронтенд | Django Templates, Bootstrap 5.3 |
| Динамический интерфейс | HTMX 1.9.10 |
| Визуализация | Chart.js 4.4.0 |
| ML-библиотеки | scikit-learn 1.4, numpy 1.26, pandas 2.2, scipy 1.12 |

---

## Системные требования

- Python 3.12 и выше
- Набор данных Kaggle `styles.csv` (Fashion Product Images Small)

---

## Быстрый старт

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py generate_benchmark_data
python manage.py runserver
```

Открыть: http://localhost:8000

---

## Подробная установка

### 1. Клонирование и установка зависимостей

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

### 2. Настройка окружения

```bash
cp .env.example .env
# Отредактировать .env
```

### 3. Миграции

```bash
python manage.py migrate
```

### 4. Получение данных Kaggle

Скачайте `styles.csv` из датасета [Fashion Product Images Small](https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-small) и поместите в:

```
data/fashion-product-images-small/styles.csv
```

### 5. Генерация бенчмарк-данных и оценка алгоритмов

```bash
python manage.py generate_benchmark_data
```

### 6. Запуск сервера

```bash
python manage.py runserver
```

---

## Команда generate_benchmark_data

Это основная команда проекта. Она:

1. Очищает базу данных
2. Импортирует реальные товары из `styles.csv` (120 товаров, 8 подкатегорий моды)
3. Создаёт 500 синтетических пользователей со структурированными предпочтениями
4. Генерирует ~6 500 взаимодействий (предпочтения + шум)
5. Обучает все пять алгоритмов рекомендаций
6. Проводит трёхкратную перекрёстную проверку (сиды: 2026, 2027, 2028)
7. Сохраняет результаты в таблицу `AlgorithmMetrics`

### Параметры

| Флаг | Описание | По умолчанию |
|------|----------|--------------|
| `--csv-file` | Путь к `styles.csv` | `data/fashion-product-images-small/styles.csv` |
| `--noise-pct` | Доля шумовых взаимодействий | `0.05` |

### Примеры

```bash
# Стандартный запуск
python manage.py generate_benchmark_data

# Указать путь к CSV
python manage.py generate_benchmark_data --csv-file /path/to/styles.csv

# Увеличить долю шума
python manage.py generate_benchmark_data --noise-pct 0.10
```

### Что создаётся

- **Товары:** 120 (8 подкатегорий × 15)
  - Topwear, Bottomwear, Shoes, Sandal, Bags, Watches, Jewellery, Fragrance
- **Пользователи:** 500
  - 350 фокусированных (одна категория)
  - 150 разнообразных (две категории)
- **Взаимодействия:** ~6 500
  - ~6 000 целевых (предпочтительные категории)
  - ~500 шумовых (случайные просмотры, 5% от целевых)
- **Оценка:** трёхкратная перекрёстная проверка, k=10 рекомендаций

---

## Остальные команды управления

```bash
# Сравнение алгоритмов
python manage.py compare_algorithms

# Повторное обучение моделей
python manage.py retrain_recommendation_models

# Миграции
python manage.py makemigrations
python manage.py migrate

# Статика
python manage.py collectstatic --noinput
```

---

## Учётные данные

### Администратор (создаётся автоматически)

```
Email:    admin@alkabry.com
Пароль:   admin123
```

### Бенчмарк-пользователи

```
Email:    pruser001@perfectreal.test ... pruser500@perfectreal.test
Пароль:   testpass2026!
```

---

## Структура проекта

```
Al-kabry/
├── config/                      # Настройки Django
├── accounts/                    # Аутентификация
├── products/                    # Каталог товаров
│   └── management/commands/
│       ├── generate_benchmark_data.py   # Основная команда
│       └── compare_algorithms.py
├── cart/                        # Корзина
├── orders/                      # Заказы
├── recommendations/             # Движок рекомендаций
│   ├── services.py              # 5 алгоритмов
│   └── models.py
├── analytics/                   # Аналитика
├── chatbot/                     # Чат-ассистент
├── templates/                   # HTML-шаблоны
├── static/                      # CSS/JS
├── data/
│   └── fashion-product-images-small/
│       └── styles.csv           # Данные Kaggle
├── thesis_colab.ipynb           # Jupyter-ноутбук
├── manage.py
├── requirements.txt
└── .env
```

---

## Результаты оценки алгоритмов

Оценка проводится на трёх сидах (2026, 2027, 2028), k = 10, разделение train/test 80/20 для каждого пользователя.

| Ранг | Алгоритм | Accuracy | HR@10 | Precision@10 | NDCG@10 | MRR |
|------|----------|----------|-------|--------------|---------|-----|
| **#1** | **Hybrid** | **85.79%** | 1.000 | 0.8367 | 0.6351 | 0.6145 |
| #2 | User-Based CF | 85.67% | 1.000 | 0.8327 | 0.6339 | 0.6150 |
| #3 | SVD | 85.61% | 0.996 | 0.8387 | 0.6346 | 0.6069 |
| #4 | Item-Based CF | 85.39% | 1.000 | 0.8273 | 0.6280 | 0.6035 |
| #5 | Content-Based | 85.04% | 1.000 | 0.8140 | 0.6254 | 0.6146 |

Гибридная система показывает наилучший результат по итоговой метрике Accuracy (85.79%), а также лучшие значения HR@10 и NDCG@10 среди всех пяти алгоритмов.

Просмотр результатов:

```bash
python manage.py compare_algorithms
```

Или через веб-интерфейс: `/analytics/` (требуется вход как `admin@alkabry.com`)

---

## Jupyter-ноутбук

Проект включает один аналитический ноутбук:

| Ноутбук | Назначение |
|---------|-----------|
| `thesis_colab.ipynb` | Реализация алгоритмов, вычисление метрик, кросс-валидация, визуализация |

Запуск:

```bash
pip install jupyter
jupyter notebook thesis_colab.ipynb
```

---

## Переменные окружения

Файл `.env`:

```env
SECRET_KEY=ваш-секретный-ключ
DEBUG=True
ALLOWED_HOSTS=*

DB_ENGINE=sqlite

# Для PostgreSQL
DB_NAME=ecommerce_alkabry
DB_USER=ecommerce_user
DB_PASSWORD=ecommerce_pass_2026
DB_HOST=localhost
DB_PORT=5432
```

---

## Развёртывание

1. `DEBUG=False` и надёжный `SECRET_KEY`
2. Перейти на PostgreSQL
3. `python manage.py collectstatic --noinput`
4. `gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3`
5. Настроить nginx для `/static/` и `/media/`

---

## Устранение неполадок

**CSV-файл не найден**

```
FileNotFoundError: Kaggle CSV not found
```

Скачайте `styles.csv` с Kaggle и поместите в `data/fashion-product-images-small/styles.csv`

**Ошибки миграций (только для разработки)**

```bash
rm -rf */migrations/0*.py
rm db.sqlite3
python manage.py makemigrations
python manage.py migrate
```

**Статические файлы**

```bash
python manage.py collectstatic --clear --noinput
```

**Module Not Found**

```bash
pip install -r requirements.txt --force-reinstall
```

---

Проект разработан в рамках дипломной работы для сравнительного исследования алгоритмов рекомендаций в контексте электронной коммерции.