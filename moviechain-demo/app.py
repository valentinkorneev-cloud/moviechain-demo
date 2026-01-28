# app.py — MovieChain (Demo / Safe publish version)
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import re
from functools import lru_cache
import time
import random

app = Flask(__name__)
CORS(app)

# ==========================
# 1) Конфигурация (SAFE)
# ==========================
GROQ_API_KEY = None  # placeholder — removed for public release
TMDB_API_KEY = None  # placeholder — removed for public release

# ==========================
# 2) Mock / локальная БД фильмов (демонстрационные данные)
# ==========================
# Небольшой набор известных фильмов для демо-режима:
MOCK_MOVIES = {
    "inception": {"title": "Inception", "year": "2010", "id": 1, "genre_ids": [878, 28], "overview": "Погружение в мир снов.", "vote_average": 8.8, "poster_url": "https://via.placeholder.com/300x450?text=Inception"},
    "interstellar": {"title": "Interstellar", "year": "2014", "id": 2, "genre_ids": [878, 18], "overview": "Путешествие через космос и время.", "vote_average": 8.6, "poster_url": "https://via.placeholder.com/300x450?text=Interstellar"},
    "arrival": {"title": "Arrival", "year": "2016", "id": 3, "genre_ids": [878, 18], "overview": "Контакт с внеземным разумом.", "vote_average": 7.9, "poster_url": "https://via.placeholder.com/300x450?text=Arrival"},
    "moon": {"title": "Moon", "year": "2009", "id": 4, "genre_ids": [878, 18], "overview": "Одиночество на лунной базе.", "vote_average": 7.9, "poster_url": "https://via.placeholder.com/300x450?text=Moon"},
    "her": {"title": "Her", "year": "2013", "id": 5, "genre_ids": [18, 10749], "overview": "Любовь в эру ИИ.", "vote_average": 8.0, "poster_url": "https://via.placeholder.com/300x450?text=Her"},
    "gladiator": {"title": "Gladiator", "year": "2000", "id": 6, "genre_ids": [36, 28, 18], "overview": "Римская эпопея о мести и чести.", "vote_average": 8.5, "poster_url": "https://via.placeholder.com/300x450?text=Gladiator"},
    "braveheart": {"title": "Braveheart", "year": "1995", "id": 7, "genre_ids": [36, 18, 28], "overview": "Историческая драма о борьбе за свободу.", "vote_average": 8.3, "poster_url": "https://via.placeholder.com/300x450?text=Braveheart"},
    "the_lion_king": {"title": "The Lion King", "year": "1994", "id": 8, "genre_ids": [16, 12, 18], "overview": "Анимационная эпопея о становлении короля.", "vote_average": 8.5, "poster_url": "https://via.placeholder.com/300x450?text=Lion+King"},
    "the_social_network": {"title": "The Social Network", "year": "2010", "id": 9, "genre_ids": [18], "overview": "История создания Facebook.", "vote_average": 7.7, "poster_url": "https://via.placeholder.com/300x450?text=Social+Network"},
}

# Минимальные fallback-постеры
DEFAULT_POSTERS = {
    'default': 'https://via.placeholder.com/300x450/95a5a6/ffffff?text=Movie+Poster'
}

# Короткая карта жанров (демо)
genre_map = {
    28: 'Боевик', 12: 'Приключения', 16: 'Мультфильм', 35: 'Комедия',
    18: 'Драма', 36: 'История', 878: 'Фантастика', 10749: 'Мелодрама'
}

# ==========================
# 3) Существующие утилиты (копия логики, но без внешних вызовов)
# ==========================
@lru_cache(maxsize=512)
def search_movie_on_tmdb_full(title, year=None):
    """
    Урезанная локальная версия поиска: пытаемся найти фильм в MOCK_MOVIES.
    Если не найден — возвращаем генерализованные метаданные.
    (В продакшне — сюда интегрировать вызов TMDb API с безопасной загрузкой ключа.)
    """
    if not title:
        return None
    key = title.lower().strip()
    # Простая нормализация
    key = re.sub(r'[^a-z0-9а-яё\s\-]', '', key)
    # Попробуем простые сопоставления
    for k, v in MOCK_MOVIES.items():
        if k in key or v['title'].lower() in key:
            return v
    # Если не найден — вернуть общий шаблон
    return {
        "title": title.title(),
        "year": year or "????",
        "id": random.randint(1000, 9999),
        "genre_ids": [],
        "overview": "",
        "vote_average": 0,
        "poster_url": DEFAULT_POSTERS['default']
    }

def get_genre_description(genre_id):
    return "разнообразные фильмы данного жанра"

# Сохраняем функции анализа намерений и т.п. (компактно)
def extract_count_from_query(query):
    query_lower = (query or "").lower()
    match = re.search(r'(\d+)\s+фильм', query_lower)
    if match:
        return min(15, max(3, int(match.group(1))))
    # Словарные замены
    if 'пять' in query_lower:
        return 5
    return None

def analyze_user_intent(query):
    query_lower = (query or "").lower()
    result = {
        'intent_type': 'abstract',
        'historical_period': None,
        'historical_confidence': 0.0,
        'historical_figure': None,
        'figure_confidence': 0.0,
        'detected_genres': [],
        'mood_keywords': [],
        'requested_count': extract_count_from_query(query),
        'blocked_titles': [],
        'year_from': None,
        'year_to': None,
        'has_year_mention': False,
        'is_historical_query': False
    }
    # Простая эвристика
    if 'средневек' in query_lower or 'античн' in query_lower or 'ренессанс' in query_lower:
        result['historical_period'] = 'средневековье'
        result['historical_confidence'] = 0.6
        result['is_historical_query'] = True
    if 'комедия' in query_lower:
        result['detected_genres'].append(35)
    if 'фантаст' in query_lower or 'космос' in query_lower:
        result['detected_genres'].append(878)
    if any(w in query_lower for w in ['грустн', 'печал', 'трагич']):
        result['mood_keywords'].append('грустный')
    if query_lower and not any(kw in query_lower for kw in ['фильм', 'посмотреть', 'рекоменд']):
        # Если похоже на название — помечаем как title
        result['intent_type'] = 'title'
    elif result['detected_genres'] or result['mood_keywords']:
        result['intent_type'] = 'description'
    return result

def validate_genre_match(movie_data, required_genres, strict_mode=False):
    if not required_genres or not movie_data:
        return True
    movie_genres = set(movie_data.get("genre_ids", []))
    required_set = set(required_genres)
    if strict_mode:
        return required_set.issubset(movie_genres)
    else:
        return len(movie_genres.intersection(required_set)) > 0

def validate_recommendations(recommendations, user_intent, liked_titles, final_genres, criteria_year_from=None, criteria_year_to=None):
    """
    Валидация рекомендаций — использует локальный поиск MOCK_MOVIES.
    """
    validated = []
    seen_titles = set(t.lower() for t in liked_titles)
    seen_ids = set()
    for rec in recommendations:
        title = rec.get("title", "").strip()
        if not title or title.lower() in seen_titles:
            continue
        movie_data = search_movie_on_tmdb_full(title, rec.get("year"))
        # Жанровая проверка (если задана)
        if final_genres and not validate_genre_match(movie_data, final_genres):
            continue
        if movie_data["id"] in seen_ids:
            continue
        validated.append({
            "title": movie_data["title"],
            "year": movie_data["year"],
            "reason": rec.get("reason", "Демонстрационная рекомендация"),
            "tmdb_id": movie_data["id"],
            "poster_url": movie_data.get("poster_url") or DEFAULT_POSTERS['default'],
            "genres": [genre_map.get(gid, 'Другое') for gid in movie_data.get("genre_ids", [])]
        })
        seen_titles.add(movie_data["title"].lower())
        seen_ids.add(movie_data["id"])
    return validated

# ==========================
# 4) Генерация демонстрационных рекомендаций (локальный AI-стаб)
# ==========================
def generate_demo_recommendations_from_query(user_query, count=5, final_genres=None, liked_titles=None, historical_period=None):
    """
    Простая 'демо-замена' вызова внешнего ИИ:
    - подбирает фильмы из MOCK_MOVIES, сопоставляя по ключевым словам или жанрам;
    - если не хватает — добавляет популярные элементы.
    """
    liked_titles = liked_titles or set()
    picks = []
    q = (user_query or "").lower()
    # Сначала — путем простого поиска по ключевым словам в MOCK_MOVIES
    for k, v in MOCK_MOVIES.items():
        if len(picks) >= count:
            break
        if k in q or any(word in v.get("overview", "").lower() for word in q.split()):
            if v['title'].lower() not in liked_titles:
                picks.append({"title": v['title'], "year": v['year'], "reason": "Подходит по ключевым словам/описанию."})
    # Затем — по жанрам (если заданы)
    if final_genres and len(picks) < count:
        for k, v in MOCK_MOVIES.items():
            if len(picks) >= count:
                break
            if set(v.get("genre_ids", [])).intersection(set(final_genres)):
                if v['title'].lower() not in liked_titles and not any(p['title'] == v['title'] for p in picks):
                    picks.append({"title": v['title'], "year": v['year'], "reason": "Соответствует выбранному жанру."})
    # Если все еще мало — просто добавляем популярные (демо)
    if len(picks) < count:
        for k, v in MOCK_MOVIES.items():
            if len(picks) >= count:
                break
            if v['title'].lower() not in liked_titles and not any(p['title'] == v['title'] for p in picks):
                picks.append({"title": v['title'], "year": v['year'], "reason": "Популярная демонстрационная рекомендация."})
    # Трим до нужного количества
    return picks[:count]

# ==========================
# 5) Эндпоинт /recommend (демо)
# ==========================
@app.route('/recommend', methods=['POST'])
def recommend():
    """
    Демонстрационный endpoint. Возвращает рекомендации, не делая сетевых вызовов
    к Groq/TMDb — полностью безопасен для публичного размещения.
    """
    try:
        start_time = time.time()
        data = request.get_json() or {}
        user_query = data.get('mood', '').strip()
        genres = data.get('genres', [])
        min_rating = float(data.get('minRating', 0.0) or 0.0)
        max_rating = float(data.get('maxRating', 10.0) or 10.0)
        count_from_criteria = min(15, max(3, int(data.get('count', 5))))
        year_from = data.get('yearFrom', '').strip()
        year_to = data.get('yearTo', '').strip()
        director = data.get('director', '').strip()
        actors = data.get('actors', '').strip()
        liked_movies = data.get('likedMovies', [])
        liked_titles = {film.get('Title', '').lower() for film in liked_movies if film.get('Title')}
        require_romance = data.get('requireRomance', False)

        # Анализ намерений (локально)
        if user_query:
            user_intent = analyze_user_intent(user_query)
        else:
            user_intent = {'intent_type': 'criteria_only', 'detected_genres': [], 'is_historical_query': False, 'requested_count': None, 'blocked_titles': []}

        final_count = user_intent.get('requested_count') or count_from_criteria
        conflict = False  # упрощенно для демо
        final_genres = user_intent.get('detected_genres') if user_intent.get('detected_genres') else genres

        # Формируем демонстрационные рекомендации (локально, без вызова ИИ)
        demo_recs = generate_demo_recommendations_from_query(user_query, count=final_count, final_genres=final_genres, liked_titles=liked_titles, historical_period=user_intent.get('historical_period'))
        validated = validate_recommendations(demo_recs, user_intent, liked_titles, final_genres)

        processing_time = round(time.time() - start_time, 2)
        return jsonify({
            "recommendations": validated,
            "analysis": user_intent,
            "processing_time": processing_time,
            "requested_count": final_count,
            "actual_count": len(validated),
            "genre_conflict": conflict,
            "note": "Демо-режим: внешние API отключены, рекомендации сгенерированы локально."
        })
    except Exception as e:
        return jsonify({"error": "Критическая ошибка сервера", "details": str(e)}), 500

if __name__ == '__main__':
    print("🚀 MovieChain (DEMO server) running - safe for public repos")
    app.run(host='127.0.0.1', port=5000, debug=True)


# Для запуска: python C:\Users\NAMETAG\Desktop\moviechain-demo\app.py