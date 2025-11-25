import pytest

from django.conf import settings
from django.test.client import Client

from news.models import Comment, News


@pytest.fixture
def news_bulk():
    return (
        News.objects.bulk_create(
            News(title=f'Новость {index}', text='Просто текст.')
            for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
        )
    )


@pytest.fixture
def news():
    return News.objects.create(
        title='Новость',
        text='Просто текст.',
    )


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create(username='Author')


@pytest.fixture
def not_author(django_user_model):
    return django_user_model.objects.create(username='NotAuthor')


@pytest.fixture
def author_client(author):
    client = Client()
    client.force_login(author)
    return client


@pytest.fixture
def not_author_client(not_author):
    client = Client()
    client.force_login(not_author)
    return client


@pytest.fixture
def comment(author, news):
    return (
        Comment.objects.create(
            text='Просто текст.',
            news=news,
            author=author,
        )
    )


@pytest.fixture
def news_pk_for_args(news):
    return (news.pk,)


@pytest.fixture
def comment_pk_for_args(comment):
    return (comment.pk,)
