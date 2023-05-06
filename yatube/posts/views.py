from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from core.utils import paginator

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all()
    page_obj = paginator(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    page_obj = paginator(request, group.posts.all())
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    post_list = user.post_set.all()
    page_obj = paginator(request, post_list)
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=user).exists()

    context = {
        'author': user,
        'page_obj': page_obj,
        'post_count': user.post_set.count(),
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id: int):
    post = get_object_or_404(Post, pk=post_id)
    post_list = post.author.post_set.count()
    comments = Comment.objects.filter(post=post)
    form = CommentForm()
    context = {
        'post': post,
        'post_count': post_list,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None
                    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user.username)
    context = {'form': form,
               'is_edit': False}
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id: int):
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:index')
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    context = {'form': form,
               'is_edit': True,
               'post_id': post_id}
    if form.is_valid():
        post.save()
        return redirect('posts:post_detail', post_id=post.id)
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    following = Follow.objects.filter(user=request.user).values_list('author',
                                                                     flat=True)
    page_obj = Post.objects.filter(author__in=following)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)
