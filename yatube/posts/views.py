from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def get_page_context(queryset, request):
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return {
        "paginator": paginator,
        "page_number": page_number,
        "page_obj": page_obj,
    }


@cache_page(20, key_prefix="index_page")
def index(request):
    context = get_page_context(
        Post.objects.select_related("author", "group"), request
    )
    return render(request, "posts/index.html", context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    context = {
        "group": group,
    }
    context.update(
        get_page_context(group.posts.select_related("author"), request)
    )
    return render(request, "posts/group_list.html", context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related("group")
    posts_count = posts.count()
    following = (
        request.user.is_authenticated
        and author.following.filter(user=request.user).exists()
    )
    context = {
        "author": author,
        "posts_count": posts_count,
        "following": following,
    }
    context.update(get_page_context(posts, request))
    return render(request, "posts/profile.html", context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author = post.author
    posts_count = Post.objects.filter(author=author).count()
    comments = post.comments.select_related("author")
    form = CommentForm()
    context = {
        "author": author,
        "post": post,
        "posts_count": posts_count,
        "comments": comments,
        "form": form,
    }
    return render(request, "posts/post_detail.html", context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == "POST" and form.is_valid():
        new_form = form.save(commit=False)
        new_form.author = request.user
        new_form.save()
        return redirect("posts:profile", new_form.author)
    context = {
        "form": form,
    }
    return render(request, "posts/create_post.html", context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect("posts:post_detail", post_id)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id)
    context = {
        "form": form,
        "is_edit": True,
        "post": post,
    }
    return render(request, "posts/create_post.html", context)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, pk=post_id)
        comment.save()
    return redirect("posts:post_detail", post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(
        author__following__user=request.user
    ).select_related("group")
    context = {}
    context.update(get_page_context(posts, request))
    return render(request, "posts/follow.html", context)


@login_required
def profile_follow(request, username):
    follow_author = get_object_or_404(User, username=username)
    if follow_author != request.user:
        Follow.objects.get_or_create(user=request.user, author=follow_author)
    return redirect("posts:profile", username)


@login_required
def profile_unfollow(request, username):
    follow_author = get_object_or_404(User, username=username)
    request.user.follower.filter(author=follow_author).delete()
    return redirect("posts:profile", username)
