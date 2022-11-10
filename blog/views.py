from django.shortcuts import render, redirect
from .models import Post, Category, Tag
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied

# Create your views here.
class PostUpdate(LoginRequiredMixin, UpdateView):
    model = Post
    fields = ['title', 'hook_text', 'content', 'head_image', 'file_upload', 'category', 'tags']

    template_name = 'blog/post_update_form.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user == self.get_object().author:
            return super(PostUpdate, self).dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(PostUpdate,self).get_context_data()
        context['categories'] = Category.objects.all()
        context['no_category_post_count'] = Post.objects.filter(category=None).count
        return context


class PostCreate(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Post
    fields = ['title', 'hook_text', 'content', 'head_image', 'file_upload', 'category']
    # 템플릿 : 모델명_form.html

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff

    def form_valid(self, form):
        current_user = self.request.user
        if current_user.is_authenticated and (current_user.is_superuser or current_user.is_staff):
            form.instance.author = current_user
            return super(PostCreate, self).form_valid(form)
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

