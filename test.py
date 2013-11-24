from pholcidae2 import Pholcidae2

class MyTestSpider(Pholcidae2):

    def before(self):
        print('-------- PRECRAWL ----------')

    def after(self):
        print('-------- POSTCRAWL ----------')

    def my_callback(self, data):
        print('-------- MY CALLBACK ----------')
        print(data.url, data.status)

    def crawl(self, data):
        print(data.url, data.status)

    settings = {
        'domain':       'www.python.org/~guido',
        'start_page':   '/',
        'valid_links':  ['(.*)'],
        'exclude_links': ['ClaymontJPEGS'],
        'precrawl': 'before',
        'postcrawl': 'after',
        'callbacks': {'(.*)': 'my_callback'}
    }

spider = MyTestSpider()
spider.start()