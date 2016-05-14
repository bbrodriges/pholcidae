PHOLCIDAE - Tiny python web crawler
=========

Pholcidae
------------
Pholcidae, commonly known as cellar spiders, are a spider family in the suborder Araneomorphae.

About
------------
Pholcidae is a tiny Python module allows you to write your own crawl spider fast and easy.

_View end of README to read about changes in v2_

Dependencies
------------
* python 2.7 or higher

Install
------------
```
pip install git+https://github.com/bbrodriges/pholcidae.git
```

Basic example
-------------

``` python
from pholcidae2 import Pholcidae

class MySpider(Pholcidae):

	def crawl(self, data):
    	print(data.url)

settings = {'domain': 'www.test.com', 'start_page': '/sitemap/'}

spider = MySpider()
spider.extend(settings)
spider.start()
```

Allowed settings
------------
Settings must be passed as dictionary to ```extend``` method of the crawler.

Params you can use:

**Required**

* **domain** _string_ - defines domain which pages will be parsed. Defines without trailing slash.

**Additional**

* **start_page** _string_ - URL which will be used as entry point to parsed site. Default: `/`
* **protocol** _string_ - defines protocol to be used by crawler. Default: `http://`
* **valid_links** _list_ - list of regular expression strings (or full URLs), which will be used to filter site URLs to be passed to `crawl()` method. Default: `['(.*)']`
* **append_to_links** _string_ - text to be appended to each link before fetching it. Default: `''`
* **exclude_links** _list_ - list of regular expression strings (or full URLs), which will be used to filter site URLs which must not be checked at all. Default: `[]`
* **cookies** _dict_ - a dictionary of string key-values which represents cookie name and cookie value to be passed with site URL request. Default: `{}`
* **headers** _dict_ - a dictionary of string key-values which represents header name and value value to be passed with site URL request. Default: `{}`
* **follow_redirects** _bool_ - allows crawler to bypass 30x headers and not follow redirects. Default: `True`
* **precrawl** _string_ - name of function which will be called before start of crawler. Default: `None`
* **postcrawl** _string_ - name of function which will be called after the end crawling. Default: `None`
* **callbacks** _dict_ - a dictionary of key-values which represents URL pattern from `valid_links` dict and string name of self defined method to get parsed data. Default: `{}`
* **proxy** _dict_ - a dictionary mapping protocol names to URLs of proxies, e.g., {'http': 'http://user:passwd@host:port'}. Default: `{}`

New in v2: 

* **silent_links** _list_ - list of regular expression strings (or full URLs), which will be used to filter site URLs which must not pass page data to callback function, yet still collect URLs from this page. Default: `[]`
* **valid_mimes** _list_ - list of strings representing valid MIME types. Only URLs that can be identified with this MIME types will be parsed. Default: `[]`
* **threads** _int_ - number of concurrent threads of pages fetchers. Default: `1`
* **with_lock** _bool_ - whether use or not lock while URLs sync. It slightly decreases crawling speed but eliminates race conditions. Default: `True`
* **hashed** _bool_ - whether or not store parsed URLs as shortened SHA1 hashes. Crawler may run a little bit slower but consumes a lot less memory. Default: `False`
* **respect_robots_txt** _bool_ - whether or not read `robots.txt` file before start and add `Disallow` directives to **exclude_links** list. Default: `True`

Response attributes
------------

While inherit Pholcidae class you can override built-in `crawl()` method to retrieve data gathered from page. Any response object will contain some attributes depending on page parsing success.

**Successful parsing**

* **body** _string_ - raw HTML/XML/XHTML etc. representation of page.
* **url** _string_ - URL of parsed page.
* **headers** _AttrDict_ - dictionary of response headers.
* **cookies** _AttrDict_ - dictionary of response cookies.
* **status** _int_ - HTTP status of response (e.g. 200).
* **match** _list_ - matched part from valid_links regex.

**Unsuccessful parsing**

* **body** _string_ - raw representation of error.
* **status** _int_ - HTTP status of response (e.g. 400). Default: 500
* **url** _string_ - URL of parsed page.

Example
------------
See ```test.py```

Note
------------
Pholcidae does not contain any built-in XML, XHTML, HTML or other parser. You can manually add any response body parsing methods using any available python libraries you want.

v2 vs v1
------------
Major changes have been made in version 2.0:
* All code has been completely rewritten from scratch
* Less abstractions = more speed
* Threads support
* Matches in page data are now list and not optional
* Option ```stay_in_domain``` has been removed. Crawler cannot break out of initial domain anymore.

There are some minor code changes which breaks backward code compatibility between version 1.x and 2.0:
* You need to explicitly pass settings to ```extend``` method of your crawler
* Option ```autostart``` has been removed. You must call ```spider.srart()``` explisitly
* Module is now called ```pholcidae2```
