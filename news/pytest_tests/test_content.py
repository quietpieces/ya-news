import pytest

from django.conf import settings
from django.urls import reverse
from pytest_lazy_fixtures import lf

from news.forms import CommentForm


pytestmark = pytest.mark.django_db


def test_news_count(news_bulk, client):
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    news_count = object_list.count()
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


def test_news_order(news_bulk, client):
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates)
    assert all_dates == sorted_dates


def test_comments_order(news, client, news_pk_for_args):
    url = reverse('news:detail', args=news_pk_for_args)
    response = client.get(url)
    # Получаем объект модели
    news_obj = response.context['news']
    all_comments = news_obj.comment_set.all()
    all_timestamps = [comment.created for comment in all_comments]
    sorted_timestamps = sorted(all_timestamps)
    assert all_timestamps == sorted_timestamps


@pytest.mark.parametrize(
        'parametrized_client, contain_form',
        (
            (lf('author_client'), True),
            (lf('client'), False),
        )
)
def test_form_for_different_users(
    parametrized_client, contain_form, news_pk_for_args
):
    url = reverse('news:detail', args=news_pk_for_args)
    response = parametrized_client.get(url)
    assert ('form' in response.context) is contain_form
    # Проверяем, что для авторизованного пользователя отображается корректная
    # форма.
    if contain_form:
        assert (
            (isinstance(response.context['form'], CommentForm)) is contain_form
        )
