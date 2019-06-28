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
    WARNING: ChannelsLiveServerTestCase has confirmed issues when running on
             Windows environment.
    """
    serve_static = True  # serve static files
    host = '0.0.0.0'  # for getting client view
    port = -1

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # check if redis running
        addr = settings.CHANNEL_LAYERS['default']['CONFIG']['hosts'][0]
        redis_running = asyncio.run(cls.redis_check(addr))
        if not redis_running:
            raise ConnectionRefusedError('Failed to connect with redis; aborting.')
        # get server address (not using localhost)
        cls.host_url = 'http://{}:'.format(settings.HOST_IP)
        # setup webdriver
        cls.selenium = WebDriver(executable_path='chromedriver')
        cls.selenium.implicitly_wait(10)  # wait for loading

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def setUp(self):
        if self.port == -1:
            self.port = self.live_server_url[-4:]
        self.selenium.get(self.host_url + self.port)

    def test_login(self):
        assert 'Portable Jukebox' in self.selenium.title
        elem = self.selenium.find_element_by_name('password')
        elem.send_keys(settings.PASSWORD)
        elem.send_keys(Keys.ENTER)
        assert 'Now Playing' in self.selenium.title

    @staticmethod
    async def redis_check(addr):
        try:
            conn = await aioredis.create_connection(addr)
        except ConnectionRefusedError:
            return False
        conn.close()
        return True
