from pholcidae import Pholcidae

class MyTestSpider(Pholcidae):

    def before(self):
        print('-------- PRECRAWL ----------')

    def after(self):
        print('-------- POSTCRAWL ----------')

    def crawl(self, data):
        print(data.url, data.status)

    settings = {
        'domain':       'www.python.org/~guido',
        'start_page':   '/',
        'valid_links':  ['(.*)'],
        'exclude_links': ['ClaymontJPEGS'],
        'precrawl': 'before',
        'postcrawl': 'after'
    }

spider = MyTestSpider()
spider.start()