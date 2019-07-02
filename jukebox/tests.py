from channels.testing import ChannelsLiveServerTestCase
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from portable_jukebox_project import settings
from .models import MusicCacheItem
import aioredis
import asyncio
import logging
import time


class ClientSeleniumTests(ChannelsLiveServerTestCase):
    """
    Selenium test cases simulating client actions.
    WARNING: ChannelsLiveServerTestCase has confirmed issues when running on Windows environment.
    """
    serve_static = True  # serve static files
    host = '0.0.0.0'  # for getting client view
    fixtures = ['testdata.json']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # disable logging
        logging.disable(logging.CRITICAL)
        # TEST ENVIRONMENT CHECK
        checker = TestUtilities()
        # 1) check if redis is running
        checker.check_redis()
        # 2) check if music cache is not empty
        checker.copy_test_music()
        # get server address (not using localhost)
        cls.host_url = 'http://{}:'.format(settings.HOST_IP)
        # setup webdriver
        options = Options()
        options.add_argument('--headless')  # run headless chrome
        options.add_argument('--window-size=1920x1080')  # set browser size
        cls.selenium = WebDriver(executable_path='./chromedriver', chrome_options=options)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        TestUtilities().clear_test_music()
        logging.disable(logging.NOTSET)
        super().tearDownClass()

    def setUp(self):
        port = self.live_server_url.split(':')[2]
        self.selenium.delete_all_cookies()
        self.selenium.get(self.host_url + port)
        form = self.selenium.find_element_by_name('password')
        form.send_keys(settings.PASSWORD)
        form.send_keys(Keys.ENTER)

    def test_login(self):
        self.assertEqual('Now Playing', self.selenium.title)
        # No music playing; skip and re-add buttons should be disabled
        skip_btn = self.selenium.find_element_by_css_selector('#btn_skip')
        self.assertTrue(skip_btn.get_attribute('disabled'))
        readd_btn = self.selenium.find_element_by_css_selector('#btn_readd')
        self.assertTrue(readd_btn.get_attribute('disabled'))
        
    def test_click_how_to_access_from_nowplaying(self):
        btn = self.selenium.find_element_by_css_selector('body > footer > a')
        btn.click()
        self.assertTrue(self.selenium.current_url.endswith('/qrcode'))
        img = self.selenium.find_element_by_css_selector('body > div.jumbotron.shadow-lg > img')
        self.assertTrue('QR Code', img.get_attribute('alt'))
        url = self.selenium.find_element_by_css_selector('body > div.jumbotron.shadow-lg > h5 > a')
        self.assertIn(settings.HOST_IP, url.text)

    def test_click_url_from_qrcode(self):
        self._get_qrcode_page()
        url = self.selenium.find_element_by_css_selector('body > div.jumbotron.shadow-lg > h5 > a')
        url.click()
        self.assertEqual('Now Playing', self.selenium.title)

    def test_click_back_from_qrcode(self):
        self._get_qrcode_page()
        btn = self.selenium.find_element_by_css_selector('body > div:nth-child(2) > a')
        btn.click()
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

    def test_search_and_add_youtube(self):
        self._get_add_page('youtube')
        form = self.selenium.find_element_by_css_selector('#youtube_search_form > div.card-body > form > div > input.form-control')
        self.assertEqual('Search YouTube..', form.get_attribute('placeholder'))
        form.send_keys('aha take on me')
        form.send_keys(Keys.ENTER)
        # Will raise NoSuchElement exception when element is not found
        self.selenium.find_element_by_css_selector('#youtube_search_result')
        # TODO: add music and check nowplaying
        # Merged search and add tests to save API call

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

    def test_add_music_from_cache(self):
        # TODO: add music from cache, check success page, check nowplaying
        self.assertTrue(True, True)

    def test_upload_music(self):
        # TODO: upload music, check success page, check nowplaying
        self.assertTrue(True, True)

    def test_click_back_from_add_file(self):
        self._get_add_page('file')
        btn = self.selenium.find_element_by_css_selector('body > div:nth-child(3) > a')
        btn.click()
        self.assertTrue(self.selenium.current_url.endswith('/add'))

    def test_skip_music(self):
        # TODO: add 1 music, click skip on nowplaying, check player stops
        self.assertTrue(True, True)

    def test_readd_music(self):
        # TODO: add 1 music, click readd on nowplaying, check item updates on next up section
        self.assertTrue(True, True)

    def test_other_client_add_music(self):
        # TODO: use 2 WebDrivers, park one on nowplaying and add music with other driver,
        #  check added music updates on parked driver
        self.assertTrue(True, True)

    def test_other_client_skip_music(self):
        # TODO: use 2 WebDrivers, check music skips on parked driver
        self.assertTrue(True, True)

    def test_other_client_readd_music(self):
        # TODO: use 2 WebDrivers, check readd button state change on parked driver, refresh and check next up section
        self.assertTrue(True, True)

    def _get_qrcode_page(self):
        """
        Sends WebDriver to qrcode page.
        :return: None
        """
        btn = self.selenium.find_element_by_css_selector('body > footer > a')
        btn.click()

    def _get_add_page(self, dest=None):
        """
        Sends WebDriver to add, add_youtube or add_file page.
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


# TODO: class HostSeleniumTests


class TestUtilities:
    """
    Pack of helper functions to use in test classes.
    """
    def check_redis(self):
        addr = settings.CHANNEL_LAYERS['default']['CONFIG']['hosts'][0]
        redis_running = asyncio.run(self.redis_check(addr))
        if not redis_running:
            msg = 'Failed to connect with redis. Test aborted.'
            raise ConnectionRefusedError(msg)

    def copy_test_music(self):
        from shutil import copyfile
        copyfile('test_noise.mp3', 'jukebox/static/music_cache/test_noise.mp3')
        if MusicCacheItem.objects.count == 0:
            raise FileNotFoundError

    def clear_test_music(self):
        import os
        os.remove('jukebox/static/music_cache/test_noise.mp3')

    @staticmethod
    async def redis_check(addr):
        try:
            conn = await aioredis.create_connection(addr)
        except ConnectionRefusedError:
            return False
        conn.close()
        return True
