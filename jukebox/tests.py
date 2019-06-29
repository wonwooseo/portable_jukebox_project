from channels.testing import ChannelsLiveServerTestCase
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.keys import Keys
from portable_jukebox_project import settings
import aioredis
import asyncio
import time


class ClientTests(ChannelsLiveServerTestCase):
    """
    Selenium test cases simulating client actions.
    WARNING: ChannelsLiveServerTestCase has confirmed issues when running on Windows environment.
    """
    serve_static = True  # serve static files
    host = '0.0.0.0'  # for getting client view

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # check if redis running
        addr = settings.CHANNEL_LAYERS['default']['CONFIG']['hosts'][0]
        redis_running = asyncio.run(cls.redis_check(addr))
        if not redis_running:
            msg = 'Failed to connect with redis. Test aborted.'
            raise ConnectionRefusedError(msg)
        # get server address (not using localhost)
        cls.host_url = 'http://{}:'.format(settings.HOST_IP)
        # setup webdriver
        cls.selenium = WebDriver(executable_path='chromedriver')

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        port = self.live_server_url.split(':')[2]
        self.selenium.get(self.host_url + port)
        form = self.selenium.find_element_by_name('password')
        form.send_keys(settings.PASSWORD)
        form.send_keys(Keys.ENTER)

    def tearDown(self):
        self.selenium.delete_all_cookies()

    def test_login(self):
        self.assertEqual('Now Playing', self.selenium.title)

    def test_click_add_from_nowplaying(self):
        btn = self.selenium.find_element_by_css_selector('#add_music')
        btn.click()
        # Will raise NoSuchElement exception when element is not found
        self.selenium.find_element_by_css_selector('#add_youtube')
        self.selenium.find_element_by_css_selector('#add_file')

    def test_click_back_from_add(self):
        self._get_add_page()
        btn = self.selenium.find_element_by_css_selector('#back')
        btn.click()
        self.assertEqual('Now Playing', self.selenium.title)

    def test_click_add_youtube_from_add(self):
        self._get_add_page()
        btn = self.selenium.find_element_by_css_selector('#add_youtube')
        btn.click()
        # Will raise NoSuchElement exception when element is not found
        self.selenium.find_element_by_css_selector('#youtube_search_form')

    def test_search_youtube(self):
        self._get_add_page('youtube')
        form = self.selenium.find_element_by_css_selector('#youtube_search_form > div.card-body > form > div > input.form-control')
        self.assertEqual('Search YouTube..', form.get_attribute('placeholder'))
        form.send_keys('aha take on me')
        form.send_keys(Keys.ENTER)
        # Will raise NoSuchElement exception when element is not found
        self.selenium.find_element_by_css_selector('#youtube_search_result')

    def test_click_back_from_add_youtube(self):
        self._get_add_page('youtube')
        btn = self.selenium.find_element_by_css_selector('body > div:nth-child(2) > a')
        btn.click()
        self.assertTrue(self.selenium.current_url.endswith('/add'))

    def test_click_add_file_from_add(self):
        self._get_add_page()
        btn = self.selenium.find_element_by_css_selector('#add_file')
        btn.click()
        # Will raise NoSuchElement exception when element is not found
        self.selenium.find_element_by_css_selector('#cache_file_list > div.card-body > ul')
        self.selenium.find_element_by_css_selector('#upload_file')

    def test_click_back_from_add_file(self):
        self._get_add_page('file')
        btn = self.selenium.find_element_by_css_selector('body > div:nth-child(3) > a')
        btn.click()
        self.assertTrue(self.selenium.current_url.endswith('/add'))

    def _get_add_page(self, dest=None):
        """
        Helper function to reach add pages.
        :param dest: youtube: reaches /add_youtube
                     file: reaches /add_file
                     None: reaches /add (Default)
        :return: None
        """
        elem = self.selenium.find_element_by_css_selector('#add_music')
        elem.click()
        if dest == 'youtube':
            elem = self.selenium.find_element_by_css_selector('#add_youtube')
            elem.click()
        elif dest == 'file':
            elem = self.selenium.find_element_by_css_selector('#add_file')
            elem.click()
        else:
            pass

    @staticmethod
    async def redis_check(addr):
        try:
            conn = await aioredis.create_connection(addr)
        except ConnectionRefusedError:
            return False
        conn.close()
        return True
