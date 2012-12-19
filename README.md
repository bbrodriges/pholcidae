pholcidae - Tiny python web crawler
=========

Pholcidae
------------

Pholcidae, commonly known as cellar spiders, are a spider family in the suborder Araneomorphae.

About
------------

Pholcidae is a tiny Python module allows you to fast and easy write your own crawl spider.

Dependencies
------------

* python >= 2.6.x

Basic example
------------

``` python
from pholcidae import Pholcidae

class MySpider(Pholcidae):

	settings = {'domain': 'www.test.com', 'start_page': '/sitemap/'}

	def crawl(self, data):
    	print(data.url)

spider = MySpider()
spider.start()
```

Allowed settings
------------

Settings must be passed as dictionary directly to subclass of Pholcidae.
Params you can use:

**Required**

* **domain** _string_ - defines domain which pages will be parsed. Defines without trailing slash.

**Additional**

* **start_page** _string_ - URL which will be used as entry point to parsed site. Default: `/`
* **protocol** _string_ - defines protocol to be used by crawler. Default: `http://`
* **stay_in_domain** _bool_ - defines ability of crawler to leave passed domain to crawl out-of-domain pages. Default: `True`
* **valid_link** _string_ - regular expression string, which will be used to filter site URLs. Default: `(.*)`
* **autostart** _bool_ - defines if crawler will be starter right after class initialization. Default: `False`
* **cookies** _dict_ - a dictionary of string key-values which represents cookie name and cookie value to be passed with site URL request. Default: `{}`

Example with all settings
------------
``` python
from pholcidae import Pholcidae

class MySpider(Pholcidae):

	settings = {
		'domain': 'www.test.com',
		'start_page': '/mypage/',
		'protocol': 'http://',
		'stay_in_domain': False,
		'valid_link': 'product-(.*).html',
		'autostart': True,
		'cookies': {
			'session': 'KSnD5KtjKDTde2Q9WxVy4iaav7a2EK73V'
		}
	}

	def crawl(self, data):
		query = 'INSERT INTO crawled (url, status, body) VALUES("%s", %i, "%s")' % (data.url, data.status, data.body)
    	database.execute(query)

spider = MySpider()
```

In this example our crawler will parse `http://www.test.com` starting with `http://www.test.com/mypage/`. It will parse only URLs with will be like `product-xxxxx.html` (example: `product-2357451.html`). Also crawler will parse any link with does not belong to `http://www.test.com`, but they must apply `valid_link` rule. Cookie header `Cookie: session=KSnD5KtjKDTde2Q9WxVy4iaav7a2EK73V` will be attached to every page request. Crawler will be started right after `spider = MySpider()`, without calling `spider.start()`.

License
------------

This code uses no license. You can use it wherever and whatever you want.