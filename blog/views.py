from django.shortcuts import render, redirect
from .models import Post, Category, Tag, Comment
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.utils.text import slugify
from .forms import CommentForm
from django.shortcuts import get_object_or_404
from django.db.models import Q

# Create your views here.


class PostUpdate(LoginRequiredMixin, UpdateView):
    model = Post
    fields = ['title', 'hook_text', 'content', 'head_image', 'file_upload', 'category'] # , 'tags'
    # 템플릿 post_form
    template_name = 'blog/post_update_form.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user == self.get_object().author:
            return super(PostUpdate, self).dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(PostUpdate,self).get_context_data()
        if self.object.tags.exists() :
            tags_str_list = list()
            for t in self.object.tags.all():
                tags_str_list.append(t.name)
            context['tags_str_default'] = ';'.join(tags_str_list)
        context['categories'] = Category.objects.all()
        context['no_category_post_count'] = Post.objects.filter(category=None).count
        return context

    def form_valid(self, form):
        response = super(PostUpdate, self).form_valid(form)
        self.object.tags.clear()
        tags_str = self.request.POST.get('tags_str')
        if tags_str:
            tags_str = tags_str.strip()
            tags_str = tags_str.replace(',', ';')
            tags_list = tags_str.split(';')
            for t in tags_list:
                t = t.strip()
                tag, is_tag_created = Tag.objects.get_or_create(name=t)
                if is_tag_created:
                    tag.slug = slugify(t, allow_unicode=True)
                    tag.save()
                self.object.tags.add(tag)
        return response

class PostCreate(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Post
    fields = ['title', 'hook_text', 'content', 'head_image', 'file_upload', 'category']  # , 'tags'
    # 템플릿 : 모델명_form.html
    # 템플릿 post_form
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff

    def form_valid(self, form):
        current_user = self.request.user
        if current_user.is_authenticated and (current_user.is_superuser or current_user.is_staff):
            form.instance.author = current_user
            response = super(PostCreate, self).form_valid(form)
            tags_str = self.request.POST.get('tags_str')
            if tags_str :
                tags_str = tags_str.strip()
                tags_str = tags_str.replace(',', ';')
                tags_list = tags_str.split(';')
                for t in tags_list :
                    t = t.strip()
                    tag, is_tag_created = Tag.objects.get_or_create(name=t)
                    if is_tag_created:
                        tag.slug = slugify(t, allow_unicode=True)
                        tag.save()
                    self.object.tags.add(tag)
            return response
        else:
            return redirect('/blog/')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(PostCreate,self).get_context_data()
        context['categories'] = Category.objects.all()
        context['no_category_post_count'] = Post.objects.filter(category=None).count
        return context

class PostList(ListView):
    model = Post
    ordering = '-pk'  # 최신 등록순으로 나열
    paginate_by = 5   # 한페이지에 게시물 5개 보여줌
    # 템플릿 없는 이유? 모델명_List.html : post_list.html 가 이미 자동으로 생성됐기 때문
    # 파라미터 모델명_list : post_list

    # 추가로 넘기고 싶은 인자 있을때 오버라이딩
    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(PostList,self).get_context_data()
        context['categories'] = Category.objects.all()
        context['no_category_post_count'] = Post.objects.filter(category=None).count
        return context

class PostDetail(DetailView):
    model = Post
    # 템플릿 모델명_Detail.html : post_detail.html
    # 파라미터 모델명 : post

    def get_context_data(self, **kwargs):
        context = super(PostDetail,self).get_context_data()
        context['categories'] = Category.objects.all()
        context['no_category_post_count'] = Post.objects.filter(category=None).count
        context['comment_form'] = CommentForm
        return context

class PostSearch(PostList):  # ListView 상속, post_list, post_list.html 자동으로 호출
    paginate_by = None  # 한 페이지당이 아닌 전체 포스트에서 검색하기 위해

    def get_queryset(self): # 검색결과를 얻는 함수
        q = self.kwargs['q']
        post_list = Post.objects.filter(
            Q(title__contains=q) | Q(tags__name__contains=q)
        ).distinct()  # title과 tags 둘 다에 있는 경우 한번만
        return post_list

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(PostSearch, self).get_context_data()
        q = self.kwargs['q']
        context['search_info'] = f'Search : {q} ({self.get_queryset().count()})'
        return context


def category_page(request,slug):
    if slug == 'no_category':
        category = '미분류'
        post_list = Post.objects.filter(category=None)
    else:
        category = Category.objects.get(slug=slug)
        post_list = Post.objects.filter(category=category)
    return render(request,'blog/post_list.html', {
        'category': category,
         'post_list': post_list,
         'categories': Category.objects.all(),
         'no_category_post_count': Post.objects.filter(category=None).count
         }
    )

def tag_page(request,slug):
    tag = Tag.objects.get(slug=slug)
    post_list = tag.post_set.all()
    return render(request,'blog/post_list.html', {
        'tag': tag,
        'post_list': post_list,
        'categories': Category.objects.all(),
        'no_category_post_count': Post.objects.filter(category=None).count
        }
    )

def new_comment(request, pk):
    if request.user.is_authenticated:
        post = get_object_or_404(Post, pk=pk)
        if request.method == 'POST':
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.post = post
                comment.author = request.user
                comment.save()
                return redirect(comment.get_absolute_url())
        else:   # GET
            return redirect(post.get_absolute_url())
    else:   # 로그인 하지 않은 사용자
        raise PermissionDenied

class CommentUpdate(LoginRequiredMixin, UpdateView):
    model = Comment
    form_class = CommentForm
    # CreateView, UpdateView 등은 form을 사용하면
    # 템플릿이 모델명_form로 자동으로 만들어짐 : comment_form

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user == self.get_object().author:
            return super(CommentUpdate, self).dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied

# FBV 스타일
#def index(request):
#    posts1 = Post.objects.all().order_by('-pk')

#   return render(
#       request,
#       'blog/index.html',
#       {'posts': posts1}
#   )

#def single_post_page(request, pk):
#   post2 = Post.objects.get(pk=pk)

#   return render(
#       request,
#       'blog/single_post_page.html',
#       {'post': post2}
#   )

