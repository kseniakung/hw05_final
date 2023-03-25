import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import CommentForm, PostForm
from posts.models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="post_author")
        cls.group = Group.objects.create(
            title="Тестовое название группы",
            slug="test-slug",
            description="Тестовое описание группы",
        )
        cls.post = Post.objects.create(
            author=cls.user, text="Тестовый пост", group=cls.group
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        """Удаляем тестовые медиа."""
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создаёт пост."""
        post_count = Post.objects.count()
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00"
            b"\x01\x00\x00\x00\x00\x21\xf9\x04"
            b"\x01\x0a\x00\x01\x00\x2c\x00\x00"
            b"\x00\x00\x01\x00\x01\x00\x00\x02"
            b"\x02\x4c\x01\x00\x3b"
        )
        uploaded = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )
        form_data = {
            "text": "Тестовый текст",
            "group": PostFormTests.group.pk,
            "image": uploaded,
        }
        response = self.authorized_client.post(
            reverse("posts:post_create"), data=form_data, follow=True
        )
        self.assertRedirects(
            response,
            reverse("posts:profile", kwargs={"username": self.user.username}),
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text="Тестовый текст",
                author=self.user,
                group=self.group,
                image="posts/small.gif",
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма редактирует пост."""
        post_count = Post.objects.count()
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00"
            b"\x01\x00\x00\x00\x00\x21\xf9\x04"
            b"\x01\x0a\x00\x01\x00\x2c\x00\x00"
            b"\x00\x00\x01\x00\x01\x00\x00\x02"
            b"\x02\x4c\x01\x00\x3b"
        )
        uploaded = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )
        form_data = {
            "text": "Измененный тестовый пост",
            "group": PostFormTests.group.pk,
            "image": uploaded,
        }
        response = self.authorized_client.post(
            reverse(
                "posts:post_edit", kwargs={"post_id": PostFormTests.post.pk}
            ),
            data=form_data,
            follow=True,
        )
        post = Post.objects.get(pk=PostFormTests.post.pk)
        self.assertRedirects(
            response,
            reverse(
                "posts:post_detail", kwargs={"post_id": PostFormTests.post.pk}
            ),
        )
        self.assertEqual(post.text, form_data["text"])
        self.assertEqual(post.group.pk, form_data["group"])
        self.assertEqual(Post.objects.count(), post_count)


class CommentPostCreateTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="post_author",)
        cls.post = Post.objects.create(
            text="Тестовый текст", author=CommentPostCreateTest.user,
        )
        cls.form = CommentForm()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_authorized_client_add_comment(self):
        """Авторизованный пользователь может добавить комментарий."""
        comment_count = self.post.comments.count()
        form_data = {
            "text": "Текст комментария",
        }
        response = self.authorized_client.post(
            reverse("posts:add_comment", kwargs={"post_id": self.post.pk}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse("posts:post_detail", kwargs={"post_id": self.post.pk}),
        )
        self.assertEqual(self.post.comments.count(), comment_count + 1)
        comment_request = self.authorized_client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.pk})
        )
        first_object = comment_request.context["comments"][0]
        self.assertEqual(first_object.text, "Текст комментария")
        self.assertEqual(first_object.author, self.user)

    def test_guest_client_add_comment(self):
        """Гость не может добавить комментарий."""
        comment_count = self.post.comments.count()
        form_data = {
            "text": "Текст комментария",
        }
        response = self.guest_client.post(
            reverse("posts:add_comment", kwargs={"post_id": self.post.pk}),
            data=form_data,
            follow=True,
        )
        login = reverse("login")
        post = reverse("posts:add_comment", kwargs={"post_id": self.post.pk})
        redirect = login + "?next=" + post
        self.assertRedirects(response, redirect)
        self.assertEqual(self.post.comments.count(), comment_count)
