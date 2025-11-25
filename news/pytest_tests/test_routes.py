"""Тестирование доступности страниц приложения."""


import pytest

from django.urls import reverse
from http import HTTPStatus
from pytest_lazy_fixtures import lf
from pytest_django.asserts import assertRedirects


@pytest.mark.django_db
@pytest.mark.parametrize(
        'name, args',
        (
            ('news:detail', lf('news_pk_for_args')),
            ('news:home', None),
            ('users:login', None),
            ('users:signup', None),
        ),
)
def test_pages_availability_for_anonymous_client(client, name, args):
    """Проверяет доступность страниц для анонимного клиента."""
    url = reverse(name, args=args)
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
        'parametrized_client, expected_status',
        (
            (lf('author_client'), HTTPStatus.OK),
            (lf('not_author_client'), HTTPStatus.NOT_FOUND),
        ),
)
@pytest.mark.parametrize(
    'name, args',
    (
        ('news:delete', lf('comment_pk_for_args')),
        ('news:edit', lf('comment_pk_for_args')),
    ),
)
def test_availability_for_comment_edit_and_delete(
    parametrized_client, expected_status, name, args
):
    """
    Доступность страниц для редактирования и удаления комментариев.

    Ожидается, что автор сможет редактировать и удалять комментарии,
    а не автор получит статус HTTP 404 (NOT FOUND).
    """
    url = reverse(name, args=args)
    response = parametrized_client.get(url)
    assert response.status_code == expected_status


@pytest.mark.parametrize(
        'name, args',
        (
            ('news:delete', lf('comment_pk_for_args')),
            ('news:edit', lf('comment_pk_for_args')),
        ),
)
def test_redirect_for_anonymous_client(client, name, args):
    """
    Редирект анонимного клиента на страницу логина.

    Для страниц редактирования и удаления комментария.
    """
    login_url = reverse('users:login')
    url = reverse(name, args=args)
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    assertRedirects(response, expected_url)
