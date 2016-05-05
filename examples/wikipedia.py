from io import StringIO

from lxml import etree

from pholcidae2 import Pholcidae


class MyWikiSpider(Pholcidae):
    def crawl(self, data):
        tree = etree.parse(StringIO(data['body']), self.html_parser)
        langs = tree.xpath(".//div[@class='central-featured']//strong/text()")

        print('Top Wikipedia languages:')
        for lang in langs:
            print(lang)


settings = {
    'protocol': 'https://',
    'domain': 'www.wikipedia.org',
    'start_page': '/',
    'exclude_links': ['(.*)'],
    'threads': 1,
}

spider = MyWikiSpider()
spider.extend(settings)
spider.html_parser = etree.HTMLParser()
spider.start()
