# Al-Kabry Ecommerce — Отчёт о завершении проекта

## Статус: завершён

---

## Что реализовано

### Платформа электронной коммерции

Полностью функциональный интернет-магазин:
- 120 реальных товаров (8 подкатегорий моды из Kaggle)
- 7 Django-приложений: accounts, products, cart, orders, recommendations, analytics, chatbot
- 15 моделей базы данных
- Аутентификация пользователей (регистрация, вход, профиль)
- Корзина с динамическими HTMX-обновлениями
- Полный цикл оформления заказа с контролем остатков
- Система отзывов и рейтингов
- История заказов

### Система рекомендаций (5 алгоритмов)

| Алгоритм | Реализация |
|----------|-----------|
| Контентная фильтрация | TF-IDF + косинусное сходство по признакам товара |
| User-Based CF | Матрица сходства пользователей |
| Item-Based CF | Матрица сходства товаров |
| SVD | TruncatedSVD, скрытые факторы |
| Гибридная система | Взвешенный ансамбль: user 50%, item 30%, content 12%, SVD 8% |

### Аналитика и сравнение

- Панель мониторинга производительности с Chart.js (только для персонала)
- Сравнение алгоритмов в реальном времени
- 3-кратная перекрёстная проверка (сиды: 2026, 2027, 2028), k=10
- Метрики: Precision@10, Recall@10, NDCG@10, Hit Rate, MRR, F1, Diversity, Coverage
- Автоматическая генерация рейтинговых отчётов

---

## Метрики проекта

| Категория | Значение |
|----------|---------|
| Django-приложения | 7 |
| Модели базы данных | 15 |
| Представления (views) | 30+ |
| HTML-шаблоны | 25+ |
| URL-маршруты | 25+ |
| Команды управления | 4 |
| Python-файлов | 50+ |
| Строк кода | 5 000+ |

### Бенчмарк-набор данных

- 120 товаров, 8 подкатегорий (Topwear, Bottomwear, Shoes, Sandal, Bags, Watches, Jewellery, Fragrance)
- 500 пользователей со структурированными профилями предпочтений
- ~6 500 взаимодействий (~6 000 предпочтений + ~500 шумовых, 5%)

---

## Ключевые файлы

| Файл | Назначение |
|------|-----------|
| `config/settings.py` | Настройки Django |
| `recommendations/services.py` | Все 5 алгоритмов (700+ строк) |
| `cart/cart.py` | Логика корзины |
| `products/management/commands/generate_benchmark_data.py` | Генерация данных |
| `products/management/commands/compare_algorithms.py` | Сравнение алгоритмов |
| `templates/base.html` | Основной шаблон Bootstrap 5 |
| `templates/analytics/dashboard.html` | Аналитика с Chart.js |

---

## Проверка системы

```bash
# Системная проверка Django
python manage.py check

# Сравнение алгоритмов
python manage.py compare_algorithms

# Применение миграций
python manage.py migrate

# Сбор статических файлов
python manage.py collectstatic
```

---

## Учётные данные

| Тип | Данные |
|-----|--------|
| Администратор | admin@alkabry.com / admin123 |
| Бенчмарк-пользователи | pruser001@perfectreal.test … pruser500@perfectreal.test / testpass2026! |

---

## Запуск проекта

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py generate_benchmark_data
python manage.py runserver
```

URL: http://localhost:8000  
Панель администратора: http://localhost:8000/admin  
Аналитика: http://localhost:8000/analytics/

---

## Технологический стек

| Уровень | Технология |
|---------|-----------|
| Бэкенд | Django 5.0.4, Python 3.12 |
| База данных | SQLite (разработка) / PostgreSQL (продакшн) |
| Фронтенд | Bootstrap 5.3, HTMX 1.9.10, Chart.js 4.4.0 |
| ML-библиотеки | scikit-learn 1.4, numpy 1.26, pandas 2.2, scipy 1.12 |
| Пакеты Django | django-crispy-forms, crispy-bootstrap5, django-filter, django-htmx |

---

## Достигнутые цели

- Полноценный Django-магазин с реальными данными
- 5 алгоритмов рекомендаций реализованы с нуля
- Воспроизводимый бенчмарк на реальных данных Kaggle
- Фреймворк сравнения алгоритмов с кросс-валидацией
- Аналитическая панель с визуализацией метрик
- Адаптивный интерфейс на Bootstrap 5 с HTMX
- Полная документация (README, PROJECT_SUMMARY, RESULTS, POSTGRESQL_SETUP)
