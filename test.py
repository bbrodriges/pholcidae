from pholcidae2 import Pholcidae


class MyTestSpider(Pholcidae):

    def before(self):
        print('-------- PRECRAWL ----------')

    def after(self):
        print('-------- POSTCRAWL ----------')

    def my_callback(self, data):
        print('-------- MY CALLBACK ----------')
        print(data['url'], data['status'], data['matches'])

    def crawl(self, data):
        print(data['url'], data['status'], data['matches'])

settings = {
    'domain': 'www.python.org/~guido',
    'start_page': '/',
    'valid_links':  ['(.*)'],
    'exclude_links': ['ClaymontJPEGS'],
    'silent_links': ['Publications.html'],
    'append_to_links': '?a=b',
    'precrawl': 'before',
    'postcrawl': 'after',
    'callbacks': {'(images.*)': 'my_callback'},
    'threads': 3,
}

spider = MyTestSpider()
spider.extend(settings)
spider.start()
