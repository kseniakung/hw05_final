from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import LEN_TEXT, Comment, Follow, Group, Post

User = get_user_model()


class PostCommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.user_2 = User.objects.create_user(
            username='another_user',
        )
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="Тестовый слаг",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user, text="Тестовый пост для проверки __str__"
        )
        cls.comment = Comment.objects.create(
            post=PostCommentModelTest.post,
            author=PostCommentModelTest.user,
            text="Тестовый комментарий",
        )

        cls.follow = Follow.objects.create(
            user=PostCommentModelTest.user_2,
            author=PostCommentModelTest.user,
        )

    def test_models_have_correct_object_names(self):
        """Верное отображение значения поля __str__ в объектах моделей."""
        post = PostCommentModelTest.post
        group = PostCommentModelTest.group
        comment = PostCommentModelTest.comment
        expected_objects_names = {
            post.text[:LEN_TEXT]: str(post),
            group.title: str(group),
            comment.text[:LEN_TEXT]: str(comment),
        }
        for item, expected_object_name in expected_objects_names.items():
            self.assertEqual(item, expected_object_name)

    def test_posts_have_help_text(self):
        """help_text тестируемых полей совпадает с ожидаемым."""
        post = PostCommentModelTest.post
        expected_post_help_texts = {
            "text": "Введите текст поста",
            "group": "Группа, к которой будет относиться пост",
            "image": "Загрузите картинку",
        }
        for field, expected_post_help_text in expected_post_help_texts.items():
            with self.subTest(field=field):
                help_text = post._meta.get_field(field).help_text
                self.assertEqual(help_text, expected_post_help_text)

    def test_posts_have_verbose_name(self):
        """verbose_name тестируемых полей совпадает с ожидаемым."""
        post = PostCommentModelTest.post
        field_verboses = {
            "text": "Текст поста",
            "pub_date": "Дата публикации",
            "author": "Автор",
            "group": "Группа",
            "image": "Картинка",
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                verbose_name = post._meta.get_field(field).verbose_name
                self.assertEqual(verbose_name, expected_value)

    def test_comment_verbose_name(self):
        """verbose_name тестируемых полей совпадает с ожидаемым."""
        comment = PostCommentModelTest.comment
        field_verboses = {
            "text": "Текст комментария",
            "created": "Дата публикации",
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                verbose_name = comment._meta.get_field(value).verbose_name
                self.assertEqual(verbose_name, expected)

    def test_comment_help_text(self):
        """help_text тестируемых полей совпадает с ожидаемым."""
        comment = PostCommentModelTest.comment
        help_text = comment._meta.get_field("text").help_text
        self.assertEqual(help_text, "Введите комментарий")

    def test_follow_verbose_name(self):
        follow = self.follow
        verbose_name = follow._meta.verbose_name
        self.assertEqual(verbose_name, "Подписка")
