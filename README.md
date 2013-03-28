PHOLCIDAE - Tiny python web crawler
=========

Pholcidae
------------

Pholcidae, commonly known as cellar spiders, are a spider family in the suborder Araneomorphae.

About
------------

Pholcidae is a tiny Python module allows you to write your own crawl spider fast and easy.

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
* **valid_links** _list_ - list of regular expression strings (or full URLs), which will be used to filter site URLs to be passed to `crawl()` method. Default: `['(.*)']`
* **exclude_links** _list_ - list of regular expression strings (or full URLs), which will be used to filter site URLs which must not be checked at all. Default: `[]`
* **autostart** _bool_ - defines if crawler will be starter right after class initialization. Default: `False`
* **cookies** _dict_ - a dictionary of string key-values which represents cookie name and cookie value to be passed with site URL request. Default: `{}`
* **headers** _dict_ - a dictionary of string key-values which represents header name and value value to be passed with site URL request. Default: `{}`
* **follow_redirects** _bool_ - allows crawler to bypass 30x headers and not follow redirects. Default: `True`
* **precrawl** _string_ - name of function which will be called before start of crawler. Default: `None`
* **postcrawl** _string_ - name of function which will be called after the end crawlering. Default: `None`

Response attributes
------------

While inhrerit Pholcidae class you can override built-in `crawl()` method to retreive data gathered from page. Any response object will contain some attributes depending on successfulness of page parsing.

**Successfull parsing**

* **body** _string_ - raw HTML/XML/XHTML etc. representation of page.
* **url** _string_ - URL of parsed page.
* **headers** _AttrDict_ - dictionary of response headers.
* **cookies** _AttrDict_ - dictionary of response cookies.
* **status** _int_ - HTTP status of response (e.g. 200).
* _optional_: **match** _str_ - matched part from valid_links regex.

**Unsuccessfull parsing**

* **body** _string_ - raw representation of error.
* **status** _int_ - HTTP status of response (e.g. 200).
* **url** _string_ - URL of parsed page.

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
		'valid_links': ['product-(.*).html'],
		'exclude_links': ['\/forum\/(.*)'],
		'autostart': True,
		'cookies': {
			'session': 'KSnD5KtjKDTde2Q9WxVy4iaav7a2EK73V'
		},
		'headers': {
			'Referer': 'http://mysite.com/'
		}
	}

	def crawl(self, data):
		query = 'INSERT INTO crawled (url, status, body) VALUES("%s", %i, "%s")' % (data.url, data.status, data.body)
    	database.execute(query)

spider = MySpider()
```

In this example our crawler will parse `http://www.test.com` starting with `http://www.test.com/mypage/`. It will pass to `crawl()` method only URLs which will be like `product-xxxxx.html` (example: `product-2357451.html`) and avoid to collect links from any URL with ".../forum/..." in it. Also crawler will parse any link with does not belong to `http://www.test.com`, but they must apply `valid_link` rule. Cookie `Cookie: session=KSnD5KtjKDTde2Q9WxVy4iaav7a2EK73V` and custom `Referer: http://mysite.com/` headers will be attached to every page request. Crawler will be started right after `spider = MySpider()`, without calling `spider.start()`.

Note
------------
Pholcidae does not contain any built-in XML, XHTML, HTML or other parser. You can manually add any response body parsing methods using any available python libraries you want.

Licence
------------

This code uses MIT License.

```
Copyright (c) 2013 bender.rodriges

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
