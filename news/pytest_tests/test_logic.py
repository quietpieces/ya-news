import pytest

from django.urls import reverse
from django.utils import timezone
from http import HTTPStatus
from pytest_django.asserts import assertFormError, assertRedirects

from news.forms import BAD_WORDS, WARNING
from news.models import Comment


@pytest.mark.django_db
def test_anonymous_client_cant_create_comment(
        client, form_data, news_pk_for_args
):
    url = reverse('news:detail', args=news_pk_for_args)
    response = client.post(url, data=form_data)
    login_url = reverse('users:login')
    expected_url = f'{login_url}?next={url}'
    assertRedirects(response, expected_url)
    assert Comment.objects.count() == 0


def test_user_can_create_comments(
    author, author_client, form_data, news_pk_for_args
):
    url = reverse('news:detail', args=news_pk_for_args)
    current_time = timezone.now()
    response = author_client.post(url, data=form_data)
    assertRedirects(response, url + '#comments')
    assert Comment.objects.count() == 1
    new_comment = Comment.objects.get()
    assert new_comment.author == author
    assert new_comment.text == form_data['text']
    assert current_time <= new_comment.created <= timezone.now()


def test_user_cant_use_bad_words(
        author_client, news_pk_for_args, form_data):
    url = reverse('news:detail', args=news_pk_for_args)
    form_data['text'] = f'Какой-то текст, {BAD_WORDS[0]}, ещё текст.'
    response = author_client.post(url, data=form_data)
    assertFormError(
        response.context['form'], 'text', errors=WARNING
    )
    assert Comment.objects.count() == 0


def test_author_can_edit_comment(
        author_client, form_data, comment,
        comment_pk_for_args, news_pk_for_args
):
    url = reverse('news:edit', args=comment_pk_for_args)
    response = author_client.post(url, data=form_data)
    assertRedirects(
        response, reverse(
            'news:detail', args=news_pk_for_args) + '#comments'
    )
    comment.refresh_from_db()
    assert comment.text == form_data['text']


def test_other_user_cant_edit_comment(
        not_author_client, form_data, comment, comment_pk_for_args
):
    url = reverse('news:edit', args=comment_pk_for_args)
    response = not_author_client.post(url, data=form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment_from_db = Comment.objects.get()
    assert comment_from_db.text == comment.text


def test_author_can_delete_comment(
        author_client, comment_pk_for_args, news_pk_for_args
):
    url = reverse('news:delete', args=comment_pk_for_args)
    response = author_client.post(url)
    assertRedirects(
        response, reverse('news:detail', args=news_pk_for_args) + '#comments'
    )
    assert Comment.objects.count() == 0


def test_other_user_cant_delete_comment(
        not_author_client, comment_pk_for_args):
    url = reverse('news:delete', args=comment_pk_for_args)
    response = not_author_client.post(url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Comment.objects.count() == 1
