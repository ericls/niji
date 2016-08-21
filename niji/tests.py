# -*- coding: utf-8 -*-
from django.test import TestCase, LiveServerTestCase
from django.utils.translation import ugettext as _
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from django.core.urlresolvers import reverse
from rest_framework.reverse import reverse as api_reverse
from django.contrib.auth.models import User
from .models import Topic, Node, Post, Notification, Appendix
from django.test.utils import override_settings
import random
import requests
import json
import time
import os

if os.environ.get('TEST_USE_FIREFOX'):
    from selenium.webdriver.firefox.webdriver import WebDriver
elif os.environ.get('TEST_USE_CHROME'):
    from selenium.webdriver.chrome.webdriver import WebDriver
else:
    from selenium.webdriver.phantomjs.webdriver import WebDriver


def login(browser, username_text, password_text):
    login_btn = browser.find_element_by_xpath(
        "//*[@id=\"main\"]/div/div[2]/div[1]/div[2]/div/div[1]/a"
    )
    login_btn.click()
    username = browser.find_element_by_name('username')
    password = browser.find_element_by_name('password')
    username.send_keys(username_text)
    password.send_keys(password_text)
    password.send_keys(Keys.RETURN)


class APITest(LiveServerTestCase):

    def setUp(self):
        self.browser = WebDriver()
        self.browser.implicitly_wait(3)
        self.n1 = Node.objects.create(
            title='TestNodeOne',
            description='The first test node'
        )
        self.u1 = User.objects.create_user(
            username='test1', email='1@q.com', password='111'
        )
        self.u1 = User.objects.create_user(
            username='test2', email='2@q.com', password='222'
        )
        self.super_user = User.objects.create_user(
            username='super', email='super@example.com', password='123'
        )
        self.super_user.is_superuser = True
        self.super_user.is_staff = True
        self.super_user.save()
        # Create 99 topics
        for i in range(1, 100):
            setattr(
                self,
                't%s' % i,
                Topic.objects.create(
                    title='Test Topic %s' % i,
                    user=self.u1,
                    content_raw='This is test topic __%s__' % i,
                    node=self.n1
                )
            )
        # Create 99 replies to self.t1
        for i in range(1, 100):
            Post.objects.create(
                topic=self.t1,
                user=self.u1,
                content_raw='This is reply to topic 1 (__%s__)' % i
            )

    def tearDown(self):
        self.browser.quit()

    def test_unauthorized_access(self):
        d = requests.get(self.live_server_url+api_reverse('niji:topic-list'))
        self.assertEqual(d.status_code, 403)
        d = requests.get(self.live_server_url+api_reverse('niji:topic-detail', kwargs={"pk": self.t1.pk}))
        self.assertEqual(d.status_code, 403)

        self.browser.get(self.live_server_url+reverse("niji:index"))
        login(self.browser, 'test1', '111')
        cookies = self.browser.get_cookies()
        s = requests.Session()
        s.headers = {'Content-Type': 'application/json'}
        for cookie in cookies:
            if cookie['name'] == 'csrftoken':
                continue
            s.cookies.set(cookie['name'], cookie['value'])
        d = s.get(self.live_server_url + api_reverse('niji:topic-list'))
        self.assertEqual(d.status_code, 403)
        d = s.get(self.live_server_url + api_reverse('niji:topic-detail', kwargs={"pk": self.t1.pk}))
        self.assertEqual(d.status_code, 403)

    def test_move_topic_up(self):
        lucky_topic1 = getattr(self, 't%s' % random.randint(1, 50))
        d = requests.patch(
            self.live_server_url + api_reverse('niji:topic-detail', kwargs={"pk": lucky_topic1.pk}),
            json.dumps({"order": 1})
        )
        self.assertEqual(d.status_code, 403)
        self.browser.get(self.live_server_url + reverse("niji:index"))
        login(self.browser, 'super', '123')
        cookies = self.browser.get_cookies()
        s = requests.Session()
        s.headers = {'Content-Type': 'application/json'}
        for cookie in cookies:
            if cookie['name'] == 'csrftoken':
                continue
            s.cookies.set(cookie['name'], cookie['value'])
        d = s.patch(
            self.live_server_url+api_reverse('niji:topic-detail', kwargs={"pk": lucky_topic1.pk}),
            json.dumps({"order": 1})
        ).json()
        self.assertEqual(d["order"], 1)

    def test_close_open_topic(self):
        lucky_topic1 = getattr(self, 't%s' % random.randint(1, 50))
        d = requests.patch(
            self.live_server_url + api_reverse('niji:topic-detail', kwargs={"pk": lucky_topic1.pk}),
            json.dumps({"closed": True})
        )
        self.assertEqual(d.status_code, 403)
        self.browser.get(self.live_server_url + reverse("niji:index"))
        login(self.browser, 'super', '123')
        cookies = self.browser.get_cookies()
        s = requests.Session()
        s.headers = {'Content-Type': 'application/json'}
        for cookie in cookies:
            if cookie['name'] == 'csrftoken':
                continue
            s.cookies.set(cookie['name'], cookie['value'])
        d = s.patch(
            self.live_server_url + api_reverse('niji:topic-detail', kwargs={"pk": lucky_topic1.pk}),
            json.dumps({"closed": True})
        ).json()
        self.assertEqual(d["closed"], True)
        d = s.patch(
            self.live_server_url + api_reverse('niji:topic-detail', kwargs={"pk": lucky_topic1.pk}),
            json.dumps({"closed": False})
        ).json()
        self.assertEqual(d["closed"], False)

    def test_hide_topic(self):
        lucky_topic1 = getattr(self, 't%s' % random.randint(1, 50))
        d = requests.patch(
            self.live_server_url + api_reverse('niji:topic-detail', kwargs={"pk": lucky_topic1.pk}),
            json.dumps({"closed": True})
        )
        self.assertEqual(d.status_code, 403)
        self.browser.get(self.live_server_url + reverse("niji:index"))
        login(self.browser, 'super', '123')
        cookies = self.browser.get_cookies()
        s = requests.Session()
        s.headers = {'Content-Type': 'application/json'}
        for cookie in cookies:
            if cookie['name'] == 'csrftoken':
                continue
            s.cookies.set(cookie['name'], cookie['value'])
        d = s.patch(
            self.live_server_url + api_reverse('niji:topic-detail', kwargs={"pk": lucky_topic1.pk}),
            json.dumps({"hidden": True})
        ).json()
        self.assertEqual(d["hidden"], True)

    def test_hide_post(self):
        lucky_post = random.choice(Post.objects.visible().all())
        d = requests.patch(
            self.live_server_url + api_reverse('niji:post-detail', kwargs={"pk": lucky_post.pk}),
            json.dumps({"hidden": True})
        )
        self.assertEqual(d.status_code, 403)
        self.browser.get(self.live_server_url + reverse("niji:index"))
        login(self.browser, 'super', '123')
        self.assertIn("Log out", self.browser.page_source)
        cookies = self.browser.get_cookies()
        s = requests.Session()
        s.headers = {'Content-Type': 'application/json'}
        for cookie in cookies:
            if cookie['name'] == 'csrftoken':
                continue
            s.cookies.set(cookie['name'], cookie['value'])
        d = s.patch(
            self.live_server_url + api_reverse('niji:post-detail', kwargs={"pk": lucky_post.pk}),
            json.dumps({"hidden": True})
        ).json()
        self.assertEqual(d["hidden"], True)


class StickToTopTest(LiveServerTestCase):

    def setUp(self):
        self.browser = WebDriver()
        self.browser.implicitly_wait(3)
        self.n1 = Node.objects.create(
            title='TestNodeOne',
            description='The first test node'
        )
        self.u1 = User.objects.create_user(
            username='test1', email='1@q.com', password='111'
        )
        self.super_user = User.objects.create_user(
            username='super', email='super@example.com', password='123'
        )
        self.super_user.is_superuser = True
        self.super_user.is_staff = True
        self.super_user.save()
        # Create 99 topics
        for i in range(1, 100):
            setattr(
                self,
                't%s' % i,
                Topic.objects.create(
                    title='Test Topic %s' % i,
                    user=self.u1,
                    content_raw='This is test topic __%s__' % i,
                    node=self.n1
                )
            )

    def tearDown(self):
        self.browser.quit()

    def test_stick_to_top_admin(self):
        self.browser.get(self.live_server_url + reverse("niji:index"))
        login(self.browser, 'super', '123')
        self.assertIn("Log out", self.browser.page_source)

        lucky_topic1 = getattr(self, 't%s' % random.randint(1, 50))

        self.browser.get(self.live_server_url+reverse('niji:topic', kwargs={"pk": lucky_topic1.pk}))
        self.browser.find_element_by_class_name('move-topic-up').click()
        up_level = WebDriverWait(
            self.browser, 10
        ).until(
            expected_conditions.presence_of_element_located(
                (By.NAME, 'move-topic-up-level')
            )
        )
        up_level = Select(up_level)
        up_level.select_by_visible_text('1')
        time.sleep(1)
        self.browser.execute_script("$('.modal-confirm').click()")
        self.browser.get(self.live_server_url+reverse('niji:index'))
        first_topic_title = self.browser.find_elements_by_class_name('entry-link')[0].text

        self.assertEqual(first_topic_title, lucky_topic1.title)


class TopicOrderingTest(LiveServerTestCase):

    def setUp(self):
        self.browser = WebDriver()
        self.browser.implicitly_wait(3)
        self.n1 = Node.objects.create(
            title='TestNodeOne',
            description='The first test node'
        )
        self.u1 = User.objects.create_user(
            username='test1', email='1@q.com', password='111'
        )
        # Create 99 topics
        for i in range(1, 100):
            setattr(
                self,
                't%s' % i,
                Topic.objects.create(
                    title='Test Topic %s' % i,
                    user=self.u1,
                    content_raw='This is test topic __%s__' % i,
                    node=self.n1
                )
            )

    def tearDown(self):
        self.browser.quit()

    def test_default_ordering_without_settings(self):
        self.browser.get(self.live_server_url+reverse("niji:index"))
        first_topic_title = self.browser.find_element_by_class_name(
            "entry-link"
        ).text
        self.assertEqual(first_topic_title, self.t99.title)
        Post.objects.create(
            topic=self.t1,
            content_raw='reply to post __1__',
            user=self.u1,
        )
        self.browser.get(self.browser.current_url)
        first_topic_title = self.browser.find_element_by_class_name(
            "entry-link"
        ).text
        self.assertEqual(first_topic_title, self.t1.title)

    @override_settings(NIJI_DEFAULT_TOPIC_ORDERING="-pub_date")
    def test_default_ordering_with_settings(self):
        self.browser.get(self.live_server_url+reverse("niji:index"))
        first_topic_title = self.browser.find_element_by_class_name(
            "entry-link"
        ).text
        self.assertEqual(first_topic_title, self.t99.title)
        Post.objects.create(
            topic=self.t1,
            content_raw='reply to post __1__',
            user=self.u1,
        )
        self.browser.get(self.browser.current_url)
        first_topic_title = self.browser.find_element_by_class_name(
            "entry-link"
        ).text
        self.assertEqual(first_topic_title, self.t99.title)

    def test_user_specified_ordering_last_replied(self):
        self.browser.get(self.live_server_url+reverse("niji:index"))
        self.browser.find_element_by_link_text(
            "Last Replied"
        ).click()
        first_topic_title = self.browser.find_element_by_class_name(
            "entry-link"
        ).text
        self.assertEqual(first_topic_title, self.t99.title)

    def test_user_specified_ordering_pub_date(self):
        Post.objects.create(
            topic=self.t1,
            content_raw='reply to post __1__',
            user=self.u1,
        )
        self.browser.get(self.live_server_url+reverse("niji:index"))
        self.browser.find_element_by_link_text(
            "Topic Date"
        ).click()
        first_topic_title = self.browser.find_element_by_class_name(
            "entry-link"
        ).text
        self.assertEqual(first_topic_title, self.t99.title)

    def test_user_specified_ordering_last_replied_pagination(self):
        self.browser.get(self.live_server_url+reverse("niji:index"))
        self.browser.find_element_by_link_text(
            "Last Replied"
        ).click()
        res = self.client.get(self.browser.current_url)
        request = res.wsgi_request
        self.assertEqual(request.GET.get("order"), "-last_replied")
        self.browser.find_element_by_link_text("»").click()
        res = self.client.get(self.browser.current_url)
        request = res.wsgi_request
        self.assertEqual(request.GET.get("order"), "-last_replied")

    def test_user_specified_ordering_node_view(self):
        Post.objects.create(
            topic=self.t1,
            content_raw='reply to post __1__',
            user=self.u1,
        )
        self.browser.get(
            self.live_server_url+reverse(
                "niji:node",
                kwargs={"pk": self.n1.pk}
            )
        )
        self.browser.find_element_by_link_text(
            "Topic Date"
        ).click()
        first_topic_title = self.browser.find_element_by_class_name(
            "entry-link"
        ).text
        self.assertEqual(first_topic_title, self.t99.title)

    def test_user_specified_ordering_search_view(self):
        Post.objects.create(
            topic=self.t1,
            content_raw='reply to post __1__',
            user=self.u1,
        )
        self.browser.get(
            self.live_server_url+reverse(
                "niji:search",
                kwargs={"keyword": "test"}
            )
        )
        self.browser.find_element_by_link_text(
            "Topic Date"
        ).click()
        first_topic_title = self.browser.find_element_by_class_name(
            "entry-link"
        ).text
        self.assertEqual(first_topic_title, self.t99.title)


class LoginRegUrlSettingsTest(LiveServerTestCase):

    def setUp(self):
        self.browser = WebDriver()
        self.browser.implicitly_wait(3)
        self.n1 = Node.objects.create(
            title='TestNodeOne',
            description='The first test node'
        )
        self.u1 = User.objects.create_user(
            username='test1', email='1@q.com', password='111'
        )
        self.t1 = Topic.objects.create(
            title='Test Topic 1',
            user=self.u1,
            content_raw='This is test topic __1__',
            node=self.n1,
        )

    def tearDown(self):
        self.browser.quit()

    @override_settings(NIJI_LOGIN_URL_NAME="niji:reg")
    def test_login_url_name(self):
        self.browser.get(self.live_server_url+reverse("niji:index"))
        login_btn = self.browser.find_element_by_link_text("Log in")
        self.assertEqual(login_btn.get_attribute("href"), self.live_server_url+reverse("niji:reg"))

        self.browser.get(self.live_server_url+reverse("niji:topic", kwargs={"pk": self.t1.pk}))
        login_link = self.browser.find_element_by_link_text("Login")
        self.assertEqual(login_link.get_attribute("href"), self.live_server_url+reverse("niji:reg"))

    @override_settings(NIJI_REG_URL_NAME="niji:login")
    def test_reg_url_name(self):
        self.browser.get(self.live_server_url+reverse("niji:index"))
        reg_btn = self.browser.find_element_by_link_text("Reg")
        self.assertEqual(reg_btn.get_attribute("href"), self.live_server_url+reverse("niji:login"))

        self.browser.get(self.live_server_url+reverse("niji:topic", kwargs={"pk": self.t1.pk}))
        reg_link = self.browser.find_element_by_link_text("Create a New User")
        self.assertEqual(reg_link.get_attribute("href"), self.live_server_url+reverse("niji:login"))


class TopicModelTest(TestCase):

    def setUp(self):
        self.n1 = Node.objects.create(
            title='TestNodeOne',
            description='The first test node'
        )
        self.u1 = User.objects.create_user(
            username='test1', email='1@q.com', password='111'
        )
        self.u2 = User.objects.create_user(
            username='test2', email='2@q.com', password='222'
        )
        self.t1 = Topic.objects.create(
            title='Test Topic 1',
            user=self.u1,
            content_raw='This is test topic __1__',
            node=self.n1,
        )
        self.t2 = Topic.objects.create(
            title='Test Topic 2',
            user=self.u1,
            content_raw='This is test topic __2__',
            node=self.n1,
        )

    def test_hidden_topic(self):
        self.assertEqual(Topic.objects.visible().count(), 2)
        self.t1.hidden = True
        self.t1.save()
        self.assertEqual(Topic.objects.visible().count(), 1)

    def test_topic_order(self):
        self.assertEqual(Topic.objects.visible().first(), self.t2)
        self.t1.order = 9
        self.t1.save()
        self.assertEqual(Topic.objects.visible().first(), self.t1)

    def test_topic_content_hash(self):
        original_hash = self.t1.raw_content_hash
        self.t1.content_raw = 'fdsfds'
        self.t1.save()
        self.assertNotEqual(original_hash, self.t1.raw_content_hash)
        self.t1.content_raw = 'This is test topic __1__'
        self.t1.save()
        self.assertEqual(original_hash, self.t1.raw_content_hash)

    def test_content_render(self):
        self.assertIn('<strong>1</strong>', self.t1.content_rendered)
        self.t1.content_raw = 'This is the __first__ topic'
        self.t1.save()
        self.assertIn('<strong>first</strong>', self.t1.content_rendered)

    def test_last_replied(self):
        p = Post()
        p.topic = self.t1
        p.content_raw = 'reply to post __1__'
        p.user = self.u1
        p.save()
        self.assertEqual(self.t1.last_replied, p.pub_date)
        p2 = Post()
        p2.topic = self.t1
        p2.content_raw = '2nd reply to post __1__'
        p2.user = self.u1
        p2.save()
        self.assertEqual(self.t1.last_replied, p2.pub_date)
        p2.delete()
        self.assertEqual(self.t1.last_replied, p.pub_date)
        p.delete()
        self.assertEqual(self.t1.last_replied, self.t1.pub_date)

    def test_reply_count(self):
        p = Post()
        p.topic = self.t1
        p.content_raw = '2nd reply to post __1__'
        p.user = self.u1
        p.save()
        self.assertEqual(self.t1.reply_count, 1)
        p.pk += 1
        p.save()
        self.assertEqual(self.t1.reply_count, 2)
        p.hidden = True
        p.save()
        self.assertEqual(self.t1.reply_count, 1)
        p.hidden = False
        p.save()
        self.assertEqual(self.t1.reply_count, 2)
        p.delete()
        self.assertEqual(self.t1.reply_count, 1)

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory')
    def test_other_user_mention(self):
        t = Topic.objects.create(
            title='topic mention test',
            user=self.u1,
            content_raw='test mention @test2',
            node=self.n1,
        )
        self.assertEqual(self.u2.received_notifications.count(), 1)
        notification = Notification.objects.get(pk=1)
        self.assertIn(
            '<a href="%s">test2</a>' % (reverse("niji:user_info", kwargs={"pk": self.u2.pk})),
            t.content_rendered
        )
        self.assertEqual(notification.topic_id, t.pk)
        self.assertEqual(notification.sender_id, self.u1.pk)
        self.assertEqual(notification.to_id, self.u2.pk)

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory')
    def test_self_mention(self):
        Topic.objects.create(
            title='topic mention test',
            user=self.u1,
            content_raw='test mention myself @test1',
            node=self.n1,
        )
        self.assertEqual(self.u1.received_notifications.count(), 0)


class PostModelTest(TestCase):

    def setUp(self):
        self.n1 = Node.objects.create(
            title='TestNodeOne',
            description='The first test node'
        )
        self.u1 = User.objects.create_user(
            username='test1', email='1@q.com', password='111'
        )
        self.u2 = User.objects.create_user(
            username='test2', email='2@q.com', password='222'
        )
        self.t1 = Topic.objects.create(
            title='Test Topic 1',
            user=self.u1,
            content_raw='This is test topic __1__',
            node=self.n1,
        )
        self.p1 = Post.objects.create(
            topic=self.t1,
            content_raw='reply to post __1__',
            user=self.u1,
        )
        self.p2 = Post.objects.create(
            topic=self.t1,
            content_raw='reply to post __2__',
            user=self.u1,
        )

    def test_content_render(self):
        self.assertIn('<strong>1</strong>', self.p1.content_rendered)
        self.p1.content_raw = 'This is the __first__ reply'
        self.p1.save()
        self.assertIn('<strong>first</strong>', self.p1.content_rendered)

    def test_hidden(self):
        self.assertEqual(self.t1.replies.visible().count(), 2)
        self.p1.hidden = True
        self.p1.save()
        self.assertEqual(self.t1.replies.visible().count(), 1)

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory')
    def test_other_user_mention(self):
        p = Post.objects.create(
            user=self.u1,
            content_raw='test mention @test2',
            topic=self.t1,
        )
        self.assertEqual(self.u2.received_notifications.count(), 1)
        notification = Notification.objects.get(pk=1)
        self.assertEqual(notification.post_id, p.pk)
        self.assertEqual(notification.sender_id, self.u1.pk)
        self.assertEqual(notification.to_id, self.u2.pk)

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory')
    def test_self_mention(self):
        Post.objects.create(
            user=self.u1,
            content_raw='test to mention myself @test1',
            topic=self.t1,
        )
        self.assertEqual(self.u1.received_notifications.count(), 0)


class AppendixModelTest(TestCase):

    def setUp(self):
        self.n1 = Node.objects.create(
            title='TestNodeOne',
            description='The first test node'
        )
        self.u1 = User.objects.create_user(
            username='test1', email='1@q.com', password='111'
        )
        self.t1 = Topic.objects.create(
            title='Test Topic 1',
            user=self.u1,
            content_raw='This is test topic __1__',
            node=self.n1,
        )
        self.a1 = Appendix.objects.create(
            topic=self.t1,
            content_raw='appendix to topic __1__',
        )

    def test_content_render(self):
        self.assertIn('<strong>1</strong>', self.a1.content_rendered)
        self.a1.content_raw = 'appendix to the __first__ topic'
        self.a1.save()
        self.assertIn('<strong>first</strong>', self.a1.content_rendered)


class VisitorTest(LiveServerTestCase):
    """
    Test as a visitor (unregistered user)
    """

    def setUp(self):
        self.browser = WebDriver()
        self.browser.implicitly_wait(3)
        self.n1 = Node.objects.create(
            title='TestNodeOne',
            description='The first test node'
        )
        self.u1 = User.objects.create_user(
            username='test1', email='1@q.com', password='111'
        )
        self.u2 = User.objects.create_user(
            username='test2', email='2@q.com', password='222'
        )

        # Create 99 topics
        for i in range(1, 100):
            setattr(
                self,
                't%s' % i,
                Topic.objects.create(
                    title='Test Topic %s' % i,
                    user=self.u1,
                    content_raw='This is test topic __%s__' % i,
                    node=self.n1
                )
            )

    def tearDown(self):
        self.browser.quit()

    def test_index(self):
        self.browser.get(self.live_server_url+reverse('niji:index'))
        self.assertIn('niji', self.browser.page_source.lower())

    def test_topic_page_content(self):
        self.browser.get(self.live_server_url+reverse('niji:topic', kwargs={'pk': self.t88.pk}))
        self.assertIn('This is test topic <strong>88</strong>', self.browser.page_source)

    def test_hidden_post(self):
        hidden_post = Post.objects.create(
            topic=self.t1,
            content_raw="i'm a reply 12138",
            user=self.u1
        )
        self.browser.get(self.live_server_url+reverse('niji:topic', kwargs={'pk': self.t1.pk}))
        self.assertIn("i'm a reply 12138", self.browser.page_source)
        hidden_post.hidden = True
        hidden_post.save()
        self.browser.get(self.browser.current_url)
        self.assertNotIn("i'm a reply 12138", self.browser.page_source)

    def test_node_page(self):
        self.browser.get(self.live_server_url+reverse('niji:node', kwargs={'pk': self.n1.pk}))
        topics = self.browser.find_elements_by_css_selector('ul.topic-list > li')
        self.assertEqual(len(topics), 30)

    def test_user_login(self):
        self.browser.get(self.live_server_url+reverse('niji:index'))
        self.assertNotIn("Log out", self.browser.page_source)
        login(self.browser, "test1", "111")
        self.assertEqual(self.browser.current_url, self.live_server_url+reverse("niji:index"))
        self.assertIn("Log out", self.browser.page_source)

    def test_usr_reg(self):
        self.browser.get(self.live_server_url+reverse('niji:index'))
        self.browser.find_element_by_link_text("Reg").click()
        self.assertEqual(self.browser.current_url, self.live_server_url+reverse("niji:reg"))
        username = self.browser.find_element_by_name('username')
        email = self.browser.find_element_by_name('email')
        password1 = self.browser.find_element_by_name('password1')
        password2 = self.browser.find_element_by_name('password2')
        username.send_keys("test3")
        password1.send_keys("333")
        password2.send_keys("333")
        email.send_keys("test3@example.com")
        password1.send_keys(Keys.RETURN)
        self.assertEqual(self.browser.current_url, self.live_server_url+reverse("niji:index"))
        self.assertIn("Log out", self.browser.page_source)
        self.assertIn("test3", self.browser.page_source)

    def test_user_topic(self):
        self.browser.get(self.live_server_url+reverse("niji:user_topics", kwargs={"pk": self.u1.id}))
        self.assertIn("UID:", self.browser.page_source)

    def test_user_info(self):
        self.browser.get(self.live_server_url+reverse("niji:user_info", kwargs={"pk": self.u1.id}))
        self.assertIn("Topics created by %s" % self.u1.username, self.browser.page_source)

    def test_search(self):
        self.browser.get(self.live_server_url+reverse("niji:search", kwargs={"keyword": "test"}))
        self.assertIn("Search: test", self.browser.page_source)

    def test_pagination(self):
        self.browser.get(self.live_server_url+reverse("niji:index", kwargs={"page": 2}))
        self.assertIn("«", self.browser.page_source)
        prev = self.browser.find_element_by_link_text("«")
        prev.click()
        self.assertNotIn("«", self.browser.page_source)
        self.assertIn("»", self.browser.page_source)
        nxt = self.browser.find_element_by_link_text("»")
        nxt.click()
        self.assertEqual(self.browser.current_url, self.live_server_url+reverse("niji:index", kwargs={"page": 2}))


class RegisteredUserTest(LiveServerTestCase):
    """
    Test as a registered user
    """

    def setUp(self):
        self.browser = WebDriver()
        self.browser.implicitly_wait(3)
        self.n1 = Node.objects.create(
            title='TestNodeOne',
            description='The first test node'
        )
        self.u1 = User.objects.create_user(
            username='test1', email='1@q.com', password='111'
        )
        self.u2 = User.objects.create_user(
            username='test2', email='2@q.com', password='222'
        )

        # Create 198 topics
        for i in range(1, 100):
            setattr(
                self,
                't%s' % i,
                Topic.objects.create(
                    title='Test Topic %s' % i,
                    user=self.u1,
                    content_raw='This is test topic __%s__' % i,
                    node=self.n1
                )
            )

        for i in range(100, 199):
            setattr(
                self,
                't%s' % i,
                Topic.objects.create(
                    title='Test Topic %s' % i,
                    user=self.u2,
                    content_raw='This is test topic __%s__' % i,
                    node=self.n1
                )
            )

    def tearDown(self):
        self.browser.quit()

    def test_edit_own_topic(self):
        self.browser.get(self.live_server_url+reverse('niji:index'))
        login(self.browser, "test1", "111")
        self.assertIn("Log out", self.browser.page_source)
        own_topic = getattr(self, "t%s" % (random.choice(range(1, 100))))
        self.browser.get(self.live_server_url+reverse("niji:topic", kwargs={"pk": own_topic.id}))
        self.browser.find_element_by_link_text("Edit").click()
        content_raw = self.browser.find_element_by_name("content_raw")
        content_raw.clear()
        content_raw.send_keys("This topic is edited")
        self.browser.find_element_by_name("submit").click()
        self.assertIn("This topic is edited", self.browser.page_source)

    def test_edit_others_topic(self):
        self.browser.get(self.live_server_url+reverse('niji:index'))
        login(self.browser, "test1", "111")
        self.assertIn("Log out", self.browser.page_source)
        others_topic = getattr(self, "t%s" % (random.choice(range(100, 199))))
        self.browser.get(self.live_server_url+reverse("niji:topic", kwargs={"pk": others_topic.id}))
        self.assertNotIn(
            "<span class=\"label label-success\">Edit</span>",
            self.browser.page_source
        )
        self.browser.get(
            self.live_server_url+reverse("niji:edit_topic", kwargs={"pk": others_topic.id})
        )
        self.assertIn("You are not allowed to edit other's topic", self.browser.page_source)

    def test_reply_topic(self):
        self.browser.get(self.live_server_url+reverse('niji:index'))
        login(self.browser, "test1", "111")
        self.assertIn("Log out", self.browser.page_source)
        topic = getattr(self, "t%s" % (random.choice(range(1, 199))))
        self.browser.get(self.live_server_url+reverse("niji:topic", kwargs={"pk": topic.id}))
        content_raw = self.browser.find_element_by_name("content_raw")
        content_raw.clear()
        content_raw.send_keys("This is a reply")
        self.browser.find_element_by_name("submit").click()
        self.assertIn("This is a reply", self.browser.page_source)

    def test_closed_topic(self):
        self.browser.get(self.live_server_url + reverse('niji:index'))
        login(self.browser, "test1", "111")
        self.assertIn("Log out", self.browser.page_source)
        topic = getattr(self, "t%s" % (random.choice(range(1, 199))))
        topic.closed = True
        topic.save()
        self.browser.get(self.live_server_url + reverse("niji:topic", kwargs={"pk": topic.id}))
        self.assertIn(_("This topic is closed"), self.browser.page_source)

    def test_create_topic(self):
        self.browser.get(self.live_server_url+reverse('niji:index'))
        login(self.browser, "test1", "111")
        self.assertIn("Log out", self.browser.page_source)
        self.browser.get(self.live_server_url+reverse("niji:create_topic"))
        node = self.browser.find_element_by_name("node")
        node = Select(node)
        title = self.browser.find_element_by_name("title")
        content_raw = self.browser.find_element_by_name("content_raw")
        node.select_by_visible_text(self.n1.title)
        title.send_keys("test title")
        content_raw.send_keys("this is content")
        self.browser.find_element_by_name("submit").click()
        self.assertIn("this is content", self.browser.page_source)

    def test_create_appendix(self):
        self.browser.get(self.live_server_url+reverse('niji:index'))
        login(self.browser, "test1", "111")
        self.assertIn("Log out", self.browser.page_source)
        own_topic = getattr(self, "t%s" % (random.choice(range(1, 100))))
        self.browser.get(self.live_server_url+reverse("niji:topic", kwargs={"pk": own_topic.id}))
        self.browser.find_element_by_link_text("Append").click()
        content_raw = self.browser.find_element_by_name("content_raw")
        content_raw.clear()
        content_raw.send_keys("This is an appendix")
        self.browser.find_element_by_name("submit").click()
        self.assertIn("This is an appendix", self.browser.page_source)
