"""
    Tests should be initiated by calling this script on command line.
"""
import unittest

if __name__ == '__main__':
    # python manage.py testserver ".testing_stuffs/testdata.json" --addrport 0.0.0.0:8000 --noinput
    loader = unittest.TestLoader()
    suite = loader.discover('jukebox/tests')
    unittest.TextTestRunner(verbosity=2).run(suite)
