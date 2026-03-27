import requests
from dataclasses import dataclass
from loguru import logger
import sys


BASE_URL = 'https://jsonplaceholder.typicode.com'

# Настройка loguru: формат, уровень, файл
# sink=sys.stdout — вывод в терминал (по умолчанию stderr)
# level="DEBUG"   — показывать все уровни (DEBUG/INFO/WARNING/ERROR)
logger.remove()  # убираем дефолтный handler
logger.add(sys.stdout, level='DEBUG', format='<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}')
logger.add('api_requests.log', level='DEBUG', rotation='1 MB')  # и в файл


# --- Клиент ---

@dataclass
class JSONPlaceholderClient:
    """Клиент для работы с JSONPlaceholder API.

    Инкапсулирует base_url и session (переиспользует TCP-соединение).
    Каждый метод = один HTTP-глагол + эндпоинт.
    """
    base_url: str = BASE_URL

    def __post_init__(self):
        self._session = requests.Session()

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = self.base_url + path
        logger.debug(f'{method} {path}')
        r = self._session.request(method, url, **kwargs)

        # rate limit — если сервер сообщает, всегда логируем
        remaining = r.headers.get('x-ratelimit-remaining')
        limit = r.headers.get('x-ratelimit-limit')
        if remaining is not None:
            level = 'WARNING' if int(remaining) < 100 else 'DEBUG'
            logger.log(level, f'rate limit: {remaining}/{limit} remaining')

        if not r.ok:
            logger.error(f'{method} {path} → {r.status_code}')
            r.raise_for_status()

        logger.debug(f'→ {r.status_code} ({r.elapsed.total_seconds():.2f}s)')
        return r

    # GET — получить список / один объект / вложенный ресурс
    def get_posts(self) -> list[dict]:
        return self._request('GET', '/posts').json()

    def get_post(self, post_id: int) -> dict:
        return self._request('GET', f'/posts/{post_id}').json()

    def get_post_comments(self, post_id: int) -> list[dict]:
        """Вложенный ресурс: комментарии конкретного поста."""
        return self._request('GET', f'/posts/{post_id}/comments').json()

    def get_posts_by_user(self, user_id: int) -> list[dict]:
        """Query-параметр: ?userId=N — фильтрация на стороне сервера."""
        return self._request('GET', '/posts', params={'userId': user_id}).json()

    def get_user(self, user_id: int) -> dict:
        return self._request('GET', f'/users/{user_id}').json()

    # POST — создать новый ресурс
    def create_post(self, title: str, body: str, user_id: int) -> dict:
        payload = {'title': title, 'body': body, 'userId': user_id}
        return self._request('POST', '/posts', json=payload).json()

    # PATCH — обновить несколько полей (не весь объект)
    def update_post_title(self, post_id: int, title: str) -> dict:
        return self._request('PATCH', f'/posts/{post_id}', json={'title': title}).json()

    # DELETE — удалить ресурс (API возвращает пустой {})
    def delete_post(self, post_id: int) -> int:
        r = self._request('DELETE', f'/posts/{post_id}')
        return r.status_code  # 200 = успех


# --- Вывод ---

def sep(title: str):
    print(f'\n{"─" * 50}')
    print(f'  {title}')
    print('─' * 50)

def show_post(post: dict):
    print(f'  [{post["id"]}] userId={post["userId"]}')
    print(f'  Заголовок : {post["title"][:60]}')
    print(f'  Тело      : {post["body"][:80].replace(chr(10), " ")}...')

def show_comment(comment: dict):
    print(f'  [{comment["id"]}] {comment["email"]}')
    print(f'  {comment["body"][:80].replace(chr(10), " ")}...')


# --- Демонстрация ---

if __name__ == '__main__':
    api = JSONPlaceholderClient()

    # 1. GET /posts — все посты (показываем первые 3)
    sep('GET /posts — все посты (первые 3)')
    posts = api.get_posts()
    print(f'  Всего постов: {len(posts)}')
    for post in posts[:3]:
        show_post(post)

    # 2. GET /posts/1 — один пост
    sep('GET /posts/33 — один пост c PostID 33')
    post = api.get_post(33)
    show_post(post)

    # 3. GET /posts/1/comments — комментарии поста
    sep('GET /posts/1/comments — комментарии (первые 2)')
    comments = api.get_post_comments(1)
    print(f'  Всего комментариев: {len(comments)}')
    for c in comments[:2]:
        show_comment(c)

    # 4. GET /posts?userId=2 — query-параметр
    sep('GET /posts?userId=4 — посты (3) конкретного пользователя с UserID 4')
    user_posts = api.get_posts_by_user(4)
    print(f'  Постов у userId=2: {len(user_posts)}')
    for post in user_posts[:3]:
        show_post(post)

    # 5. GET /users/1 — данные пользователя
    sep('GET /users/1 — профиль пользователя')
    user = api.get_user(1)
    print(f'  Имя    : {user["name"]}')
    print(f'  Email  : {user["email"]}')
    print(f'  Сайт   : {user["website"]}')
    print(f'  Компания: {user["company"]["name"]}')

    # 6. POST /posts — создать новый пост
    sep('POST /posts — создать пост')
    new_post = api.create_post(
        title='Мой первый API-пост',
        body='Тело поста через requests.Session и dataclass.',
        user_id=1,
    )
    # API возвращает объект с id=101 (fake, не сохраняется)
    print(f'  Создан: id={new_post["id"]}, title="{new_post["title"]}"')

    # 7. PATCH /posts/1 — частичное обновление
    sep('PATCH /posts/1 — обновить только заголовок')
    updated = api.update_post_title(1, 'Новый заголовок через PATCH')
    print(f'  id={updated["id"]}, title="{updated["title"]}"')

    # 8. DELETE /posts/1 — удалить
    sep('DELETE /posts/1 — удалить пост')
    status = api.delete_post(1)
    print(f'  Статус: {status} (200 = успешно удалён, данные на сервере не меняются — это fake API)')
