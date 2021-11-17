
from ytInter import *
import unittest

yt = YT()

class TestYT(unittest.TestCase):

    def test_understanding(self):
        pass
    
    def test_generalQuery(self):
        resp = yt.generalQuery("Roar Katy Perry")
        print(resp)
        self.assertTrue("Roar" in resp)
        self.assertTrue("Katy Perry" in resp)
        self.assertTrue("PRISM" in resp)
        self.assertTrue("sakjlfnl" not in resp)
    
    def test_topCharts(self):
        lines = yt.topChartsQuery(10)
        for line in lines:
            print(line)
        self.assertTrue(len(lines) == 11)