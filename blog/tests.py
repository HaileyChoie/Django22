from django.test import TestCase, Client
from bs4 import BeautifulSoup
from .models import Post
from django.contrib.auth.models import User

# Create your tests here.
class TestView(TestCase):

    def setUp(self):
        self.client = Client()
        self.user_kim = User.objects.create_user(username="kim", password="somepassword")
        self.user_lee = User.objects.create_user(username="lee", password="somepassword")

    def nav_test(self, soup):
        navbar = soup.nav
        self.assertIn('Blog', navbar.text)
        self.assertIn('About Me', navbar.text)

    def test_post_list(self):
        # 포스트 목록 페이지 가져오기
        response = self.client.get('/blog/')
        # response 결과가 정상적인지
        self.assertEqual(response.status_code, 200)

        soup = BeautifulSoup(response.content, 'html.parser')

        # title이 정상적으로 보이는지
        self.assertEqual(soup.title.text, 'Blog')

        # navbar가 정상적으로 보이는지
        #navbar = soup.nav
        #self.assertIn('Blog', navbar.text)
        #self.assertIn('About Me', navbar.text)
        self.nav_test(soup)

        # Post가 정상적으로 보이는지
        # 1. 맨 처음엔 포스트가 하나도 안보임
        self.assertEqual(Post.objects.count(), 0)
        main_area = soup.find('div', id="main-area")
        self.assertIn('아무 게시물이 없습니다.', main_area.text)
        # 2. Post가 있는 경우
        post_001 = Post.objects.create(title="첫번째 포스트", content="첫번째 포스트입니다.",
                                       author=self.user_kim)
        post_002 = Post.objects.create(title="두번째 포스트", content="두번째 포스트입니다.",
                                       author=self.user_lee)
        self.assertEqual(Post.objects.count(), 2)

        # 포스트 목록 페이지를 새로고침 했을 때
        response = self.client.get('/blog/')
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')

        # main area에 포스트 2개 제목이 있는지
        main_area = soup.find('div', id="main-area")
        self.assertIn(post_001.title, main_area.text)
        self.assertIn(post_002.title, main_area.text)

        # main area에 포스트 2개 작성자가 있는지
        self.assertIn(post_001.author.username.upper(), main_area.text)
        self.assertIn(post_002.author.username.upper(), main_area.text)

        # '아직 게시물이 없습니다'가 더이상 나타나지 않는지
        self.assertNotIn('아무 게시물이 없습니다.', main_area.text)


    def test_post_detail(self):
        # 상세 페이지가 있으려면 적어도 포스트 하나가 필요함
        post_001 = Post.objects.create(title="첫번째 포스트", content="첫번째 포스트입니다.",
                                       author=self.user_kim)
        self.assertEqual(post_001.get_absolute_url(), '/blog/1/')

        # 포스트 상세 페이지 가져오기
        response = self.client.get(post_001.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content, 'html.parser')

        # navbar가 정상적으로 보이는지
        #navbar = soup.nav
        #self.assertIn('Blog', navbar.text)
        #self.assertIn('AboutMe', navbar.text)
        self.nav_test(soup)

        # title이 정상적으로 보이는지
        self.assertIn(post_001.title, soup.title.text)

        # 포스트 안의 내용 있는지
        main_area = soup.find('div', id='main-area')
        post_area = main_area.find('div', id='post-area')
        self.assertIn(post_001.title, post_area.text)
        self.assertIn(post_001.content, post_area.text)
        self.assertIn(post_001.author.username.upper(), post_area.text)





