from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import unittest
import socket
import aioredis
import asyncio
import time


soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
soc.connect(('8.8.8.8', 80))
GLOBAL_HOST = soc.getsockname()[0]
soc.close()


class ClientSeleniumTests(unittest.TestCase):
    """
    Selenium test cases simulating client actions.
    """

    host = 'http://{}:8001'.format(GLOBAL_HOST)  # for getting client view

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # TEST ENVIRONMENT CHECK
        checker = TestUtilities()
        # 1) check if redis is running
        checker.check_redis()
        # 2) check if music cache is not empty
        checker.copy_test_music()
        # setup webdriver
        cls.drv_options = Options()
        cls.drv_options.add_argument('--headless')  # run headless chrome
        cls.drv_options.add_argument('--window-size=1920x1080')  # set browser size
        cls.selenium = WebDriver(executable_path='./chromedriver', chrome_options=cls.drv_options)
        cls.selenium2 = WebDriver(executable_path='./chromedriver', chrome_options=cls.drv_options)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        cls.selenium2.quit()
        TestUtilities().clear_test_music()
        super().tearDownClass()

    def setUp(self):
        self.selenium.get(self.host)

    def test_01_login(self):
        self.selenium.get(self.host)
        form = self.selenium.find_element_by_name('password')
        form.send_keys(1234)  # TODO: read from config or settings
        form.send_keys(Keys.ENTER)
        time.sleep(1)  # wait for update
        self.assertEqual('Now Playing', self.selenium.title)
        # No music playing; skip and re-add buttons should be disabled
        skip_btn = self.selenium.find_element_by_css_selector('#btn_skip')
        self.assertTrue(skip_btn.get_attribute('disabled'))
        readd_btn = self.selenium.find_element_by_css_selector('#btn_readd')
        self.assertTrue(readd_btn.get_attribute('disabled'))
        
    def test_02_click_how_to_access_from_nowplaying(self):
        btn = self.selenium.find_element_by_css_selector('body > footer > a')
        btn.click()
        self.assertTrue(self.selenium.current_url.endswith('/qrcode'))
        img = self.selenium.find_element_by_css_selector('body > div.jumbotron.shadow-lg > img')
        self.assertEqual('QR Code', img.get_attribute('alt'))
        url = self.selenium.find_element_by_css_selector('body > div.jumbotron.shadow-lg > h5 > a')
        self.assertIn(self.host, url.text)

    def test_03_click_url_from_qrcode(self):
        self._get_qrcode_page()
        url = self.selenium.find_element_by_css_selector('body > div.jumbotron.shadow-lg > h5 > a')
        url.click()
        self.assertEqual('Now Playing', self.selenium.title)

    def test_04_click_back_from_qrcode(self):
        self._get_qrcode_page()
        btn = self.selenium.find_element_by_css_selector('body > div:nth-child(2) > a')
        btn.click()
        self.assertEqual('Now Playing', self.selenium.title)

    def test_05_click_add_from_nowplaying(self):
        btn = self.selenium.find_element_by_css_selector('#add_music')
        btn.click()
        # Will raise NoSuchElement exception when element is not found
        self.selenium.find_element_by_css_selector('#add_youtube')
        self.selenium.find_element_by_css_selector('#add_file')

    def test_06_click_back_from_add(self):
        self._get_add_page()
        btn = self.selenium.find_element_by_css_selector('#back')
        btn.click()
        self.assertEqual('Now Playing', self.selenium.title)

    def test_07_click_add_youtube_from_add(self):
        self._get_add_page()
        btn = self.selenium.find_element_by_css_selector('#add_youtube')
        btn.click()
        # Will raise NoSuchElement exception when element is not found
        self.selenium.find_element_by_css_selector('#youtube_search_form')

    def test_08_search_and_add_youtube(self):
        self._get_add_page('youtube')
        form = self.selenium.find_element_by_css_selector('#youtube_search_form > div.card-body > form > div > input.form-control')
        self.assertEqual('Search YouTube..', form.get_attribute('placeholder'))
        form.send_keys('aha take on me')
        form.send_keys(Keys.ENTER)
        # Will raise NoSuchElement exception when element is not found
        self.selenium.find_element_by_css_selector('#youtube_search_result')
        # Merged search and add tests to save API call
        btn = self.selenium.find_elements_by_class_name('btn-outline-dark')[0]  # selector / xpath not consistent
        title = btn.text.strip()
        btn.click()
        self.assertEqual('Successfully Added!', self.selenium.title)
        btn = self.selenium.find_element_by_css_selector('body > div > a')
        btn.click()
        # Now at /nowplaying
        time.sleep(1)  # wait for music info updates by websocket
        title_h = self.selenium.find_element_by_css_selector('#title').text.strip()
        self.assertEqual(title, title_h)
        # cleanup
        self._skip_music()

    def test_09_click_back_from_add_youtube(self):
        self._get_add_page('youtube')
        btn = self.selenium.find_element_by_css_selector('body > div:nth-child(2) > a')
        btn.click()
        self.assertTrue(self.selenium.current_url.endswith('/add'))

    def test_10_click_add_file_from_add(self):
        self._get_add_page()
        btn = self.selenium.find_element_by_css_selector('#add_file')
        btn.click()
        # Will raise NoSuchElement exception when element is not found
        self.selenium.find_element_by_css_selector('#cache_file_list > div.card-body > ul')
        self.selenium.find_element_by_css_selector('#upload_file')

    def test_11_add_music_from_cache(self):
        self._get_add_page('file')
        li = self.selenium.find_elements_by_class_name('list-group-item')[0]  # xpath / selector not consistent
        desc = li.find_element_by_tag_name('b').text
        btn = li.find_element_by_tag_name('button')
        btn.click()
        self.assertEqual('Successfully Added!', self.selenium.title)
        btn = self.selenium.find_element_by_css_selector('body > div > a')
        btn.click()
        # Now at /nowplaying
        time.sleep(1)  # wait for music info updates by websocket
        title_h = self.selenium.find_element_by_css_selector('#title').text.strip()
        artist_h = self.selenium.find_element_by_css_selector('#artist').text.strip()
        self.assertIn(title_h, desc)
        self.assertIn(artist_h, desc)
        # cleanup
        self._skip_music()

    def test_12_upload_music(self):
        import os
        self._get_add_page('file')
        form = self.selenium.find_element_by_css_selector('#upload_file > div > input.form-control-file')
        form.send_keys(os.getcwd() + '/.testing_stuffs/test_noise2.mp3')
        self.selenium.find_element_by_css_selector('#upload_form > div.card-footer.text-center > button').click()
        self.assertEqual('Successfully Added!', self.selenium.title)
        btn = self.selenium.find_element_by_css_selector('body > div > a')
        btn.click()
        # Now at /nowplaying
        time.sleep(1)  # wait for music info updates by websocket
        title_h = self.selenium.find_element_by_css_selector('#title').text.strip()
        self.assertEqual('Test Whitenoise', title_h)
        # cleanup
        self._skip_music()

    def test_13_click_back_from_add_file(self):
        self._get_add_page('file')
        btn = self.selenium.find_element_by_css_selector('body > div:nth-child(3) > a')
        btn.click()
        self.assertTrue(self.selenium.current_url.endswith('/add'))

    def test_14_skip_music(self):
        self._add_one_music()
        btn = self.selenium.find_element_by_css_selector('#btn_skip')
        btn.click()
        time.sleep(2)  # wait for refresh and music info update by websockets
        title = self.selenium.find_element_by_css_selector('#title').text
        self.assertEqual('No music playing now..', title)

    def test_15_readd_music(self):
        self._add_one_music()
        time.sleep(1)  # wait for websocket update
        btn = self.selenium.find_element_by_css_selector('#btn_readd')
        btn.click()
        self.selenium.implicitly_wait(5)  # wait for javascript DOM edit
        btn = self.selenium.find_element_by_css_selector('#btn_readd')
        self.assertTrue(btn.get_attribute('disabled'))
        self.selenium.refresh()
        time.sleep(1)  # wait for websocket update
        self.selenium.implicitly_wait(5)  # wait for javascript DOM edit
        btn = self.selenium.find_element_by_css_selector('#btn_readd')
        self.assertTrue(btn.get_attribute('disabled'))
        # Will raise NoSuchElement exception when element is not found
        self.selenium.find_element_by_css_selector('body > div:nth-child(2) > div.card-body > ul > li')
        # cleanup
        self._skip_music()
        time.sleep(1)
        self._skip_music()

    def test_16_other_client_add_music(self):
        self._start_new_driver()
        self.selenium2.find_element_by_css_selector('#add_music').click()
        self.selenium2.find_element_by_css_selector('#add_file').click()
        li = self.selenium2.find_elements_by_class_name('list-group-item')[0]  # xpath / selector not consistent
        desc = li.find_element_by_tag_name('b').text
        li.find_element_by_tag_name('button').click()
        time.sleep(1)  # wait for update
        title_h = self.selenium.find_element_by_css_selector('#title').text.strip()
        artist_h = self.selenium.find_element_by_css_selector('#artist').text.strip()
        self.assertIn(title_h, desc)
        self.assertIn(artist_h, desc)

    def test_17_other_client_skip_music(self):
        self.selenium2.get(self.host)
        time.sleep(1)  # wait for update
        # currently shows music added on previous testcase
        self.selenium2.find_element_by_css_selector('#btn_skip').click()
        time.sleep(1)  # wait for update
        title = self.selenium.find_element_by_css_selector('#title').text
        self.assertEqual('No music playing now..', title)

    def test_18_other_client_readd_music(self):
        # add music
        self.selenium2.find_element_by_css_selector('#add_music').click()
        self.selenium2.find_element_by_css_selector('#add_file').click()
        li = self.selenium2.find_elements_by_class_name('list-group-item')[0]  # xpath / selector not consistent
        li.find_element_by_tag_name('button').click()
        # click readd on /nowplaying
        self.selenium2.get(self.host)
        self.selenium2.find_element_by_css_selector('#btn_readd').click()
        time.sleep(1)  # wait for update
        btn = self.selenium.find_element_by_css_selector('#btn_readd')
        self.assertTrue(btn.get_attribute('disabled'))
        # cleanup
        self._skip_music()
        time.sleep(1)
        self._skip_music()

    def _get_qrcode_page(self):
        """
        Sends WebDriver to qrcode page. Should be called at /nowplaying.
        :return: None
        """
        btn = self.selenium.find_element_by_css_selector('body > footer > a')
        btn.click()

    def _get_add_page(self, dest=None):
        """
        Sends WebDriver to add, add_youtube or add_file page. Should be called at /nowplaying.
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

    def _add_one_music(self):
        """
        Adds one music to playlist and returns to /nowplaying. Should be called at /nowplaying.
        :return: None
        """
        self._get_add_page('file')
        li = self.selenium.find_elements_by_class_name('list-group-item')[0]  # xpath / selector not consistent
        li.find_element_by_tag_name('button').click()
        self.selenium.find_element_by_css_selector('body > div > a').click()

    def _skip_music(self):
        """
        Skips music on /nowplaying.
        :return: None
        """
        btn = self.selenium.find_element_by_css_selector('#btn_skip')
        btn.click()

    def _start_new_driver(self):
        self.selenium2.get(self.host)
        form = self.selenium2.find_element_by_name('password')
        form.send_keys(1234)
        form.send_keys(Keys.ENTER)


class HostSeleniumTests(unittest.TestCase):
    """
    Selenium test cases simulating host actions.
    """

    client_addr = 'http://{}:8001'.format(GLOBAL_HOST)  # for getting client view
    host_addr = 'http://127.0.0.1:8001'  # for getting host view

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # TEST ENVIRONMENT CHECK
        checker = TestUtilities()
        # 1) check if redis is running
        checker.check_redis()
        # 2) check if music cache is not empty
        checker.copy_test_music()
        # setup webdriver
        cls.drv_options = Options()
        cls.drv_options.add_argument('--headless')  # run headless chrome
        cls.drv_options.add_argument('--window-size=1920x1080')  # set browser size
        cls.selenium_h = WebDriver(executable_path='./chromedriver', chrome_options=cls.drv_options)
        cls.selenium_c = WebDriver(executable_path='./chromedriver', chrome_options=cls.drv_options)

    @classmethod
    def tearDownClass(cls):
        import os
        cls.selenium_h.quit()
        cls.selenium_c.quit()
        os.remove('jukebox/static/music_cache/test_noise.mp3')
        super().tearDownClass()

    def setUp(self):
        self.selenium_h.get(self.host_addr)

    def test_01_host_player(self):
        self.assertEqual('Now Playing (Host)', self.selenium_h.title)
        time.sleep(1)  # wait for update
        title = self.selenium_h.find_element_by_css_selector('#title').text
        self.assertEqual('No music playing now..', title)
        self.selenium_h.find_element_by_css_selector('#skip_label')
        self.selenium_h.find_element_by_css_selector('#readd_label')
        img = self.selenium_h.find_element_by_css_selector('body > div > div:nth-child(2) > div.card-body > img')
        self.assertEqual('QR Code', img.get_attribute('alt'))
        link = self.selenium_h.find_element_by_css_selector('body > div > div:nth-child(2) > div.card-body > h5 > a')
        self.assertIn(self.client_addr, link.text)

    def test_02_client_add_youtube_music(self):
        self._start_client_driver()
        pass

    def test_03_client_add_cache_music(self):
        self._get_client_add_page('file')
        li = self.selenium_c.find_elements_by_class_name('list-group-item')[0]  # xpath / selector not consistent
        desc = li.find_element_by_tag_name('b').text
        li.find_element_by_tag_name('button').click()
        self.selenium_c.find_element_by_css_selector('body > div > a').click()
        # client now at /nowplaying
        time.sleep(1)  # wait for music info updates by websocket
        title_h = self.selenium_h.find_element_by_css_selector('#title').text.strip()
        self.assertIn(title_h, desc)
        # cleanup
        self._skip_music()

    def test_04_client_skips_music(self):
        pass

    def test_05_client_readds_music(self):
        pass

    def _get_client_add_page(self, dest=None):
        """
        Sends Client WebDriver to add, add_youtube or add_file page. Should be called at /nowplaying.
        :param dest: youtube: reaches /add_youtube
                     file: reaches /add_file
                     None: reaches /add (Default)
        :return: None
        """
        elem = self.selenium_c.find_element_by_css_selector('#add_music')
        elem.click()
        if dest == 'youtube':
            elem = self.selenium_c.find_element_by_css_selector('#add_youtube')
            elem.click()
        elif dest == 'file':
            elem = self.selenium_c.find_element_by_css_selector('#add_file')
            elem.click()
        else:
            pass

    def _skip_music(self):
        """
        Skips music on client's /nowplaying.
        :return: None
        """
        btn = self.selenium_c.find_element_by_css_selector('#btn_skip')
        btn.click()

    def _start_client_driver(self):
        self.selenium_c.get(self.client_addr)
        form = self.selenium_c.find_element_by_name('password')
        form.send_keys(1234)
        form.send_keys(Keys.ENTER)


class TestUtilities:
    """
    Pack of helper functions to use in test classes.
    """
    def check_redis(self):
        addr = ('127.0.0.1', 6379)
        redis_running = asyncio.run(self.redis_check(addr))
        if not redis_running:
            msg = 'Failed to connect with redis. Test aborted.'
            raise ConnectionRefusedError(msg)

    def copy_test_music(self):
        from shutil import copyfile
        copyfile('.testing_stuffs/test_noise.mp3', 'jukebox/static/music_cache/test_noise.mp3')

    def clear_test_music(self):
        import os
        os.remove('jukebox/static/music_cache/test_noise.mp3')
        os.remove('jukebox/static/music_cache/test_noise2.mp3')

    @staticmethod
    async def redis_check(addr):
        try:
            conn = await aioredis.create_connection(addr)
        except ConnectionRefusedError:
            return False
        conn.close()
        return True
