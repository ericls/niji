# -*- coding: utf-8 -*-
from django.test import TestCase, LiveServerTestCase
from django.utils.translation import ugettext as _
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from .models import Topic, Node, Post, Notification, Appendix
from django.test.utils import override_settings
import random


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
