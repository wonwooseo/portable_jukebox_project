"""
    Tests should be initiated by calling this script on command line.
"""
import unittest
import subprocess
import time

if __name__ == '__main__':
    p = subprocess.Popen(['python', 'manage.py', 'testserver', '.testing_stuffs/testdata.json',
                          '--addrport', '0.0.0.0:8001', '--noinput'])
    print('Waiting testserver to start up..')
    time.sleep(5)  # give time for test server to start up
    loader = unittest.TestLoader()
    suite = loader.discover('jukebox/tests')
    unittest.TextTestRunner(verbosity=2).run(suite)
    p.kill()
    # redis-cli flushall
