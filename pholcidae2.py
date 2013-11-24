# -*- coding: UTF-8 -*-

from urlparse import urlparse
from threading import Thread
import httplib, sys
from Queue import Queue


class Pholcidae2:

    """" Pholcidae2 is a small and fast web crawler with threading. """

    def __init__(self):

        """
            @return void

            Creates Pholcidae instance and updates default settings dict.
        """

        concurrent = 200

        self.q = Queue(concurrent*2)
        for i in range(concurrent):
            t = Thread(target=self.do_work)
            t.daemon = True
            t.start()

        for url in ['http://google.com', 'http://ya.ru', 'http://auto.ru', 'http://rodriges.org', 'http://avito.ru', 'http://twitter.com']:
            self.q.put(url.strip())
        self.q.join()

    def do_work(self):
        while True:
            url = self.q.get()
            status, url = self.get_status(url)
            self.do_something_with_result(status, url)
            self.q.task_done()

    def get_status(self, ourl):
        try:
            url = urlparse(ourl)
            conn = httplib.HTTPConnection(url.netloc)
            conn.request("HEAD", url.path)
            res = conn.getresponse()
            return res.status, ourl
        except:
            return "error", ourl

    def do_something_with_result(self, status, url):
        print status, url


sprider = Pholcidae2()