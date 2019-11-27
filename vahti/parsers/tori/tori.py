import logging
from datetime import datetime
from textwrap import shorten

from vahti.cliargs import arg
from vahti.parser import Parser
from vahti.helpers import convert_str_to_float
# TODO: add other parameters
# TODO: check for and parse all pages
# TODO: add sorting
# TODO: limit number of items

# TODO: extend vahti and control own cli

logger = logging.getLogger("vahti.tori")


@arg("-r", "--region", dest="region", default="koko_suomi", help="filter by region")
@arg("-s","--sort", dest="sort", default="price", help="sort result by price or title", type=str,choices=["price","title"])
class Tori(Parser):
    """A parser for tori.fi"""

    def __init__(self, params=None, config=None):
        if not params:
            params = {"st": "s"}
        super().__init__(params, config)
        self.url_template = "https://www.tori.fi/{region}/".format
        self.item_format = "{date:>12} {title:40} {price:>6} {link}".format

        if "region" not in config:
            config["region"] = "uusimaa"

    def set_query(self, query=""):
        self.params["q"] = query

    def parse(self, html):
        soup = super().parse(html)
        items = soup.find_all("a", class_="item_row")

        result = {}
        now = datetime.utcnow()

        for item in items:
            item_id = item.get("id").split("_")[1]
            title_long = item.find("div", class_="li-title").text
            new_item = {
                "title": shorten(title_long, width=30, placeholder=".."),
                "title_long": title_long,
                "date": " ".join(item.find("div", class_="date_image").text.split()),
                "price": item.find("p", class_="list_price").text,
                "link": f"https://www.tori.fi/vi/{item_id}.htm",
                "seen": now,
            }
            result[item_id] = new_item
        self.print_result(result,self.config)
        return result

    def print_result(self,result,config):
        sorted_list=[]
        dict_list=[result[item] for item in result]
        if not dict_list:
            return 1
        if not config:
            return 1
        if "sort" not in config:
            pass
        elif config.get("sort") == "price":
            sorted_list = self.sort_price(dict_list)
        else:
            sorted_list = self.sort_title(dict_list)
        for item in sorted_list:
            logger.debug(self.item_format(**item))

    def sort_price(self,unsortlist):
        if not unsortlist:
            return 1
        sorted_list = sorted(unsortlist, key=lambda k: convert_str_to_float(k["price"]))
        return sorted_list

    def sort_title(self,unsortlist):
        if not unsortlist:
            return 1
        sorted_list = sorted(unsortlist, key=lambda k:(k["title"]))
        return sorted_list
    @staticmethod
    def get_pages_url(soup):
        return [i.get("url") for i in soup.select(".long_pagination a")]

    @staticmethod
    def get_pages_count(soup):
        return len(Tori.get_pages_url(soup))

    async def get_options(self, html_id):
        html = await super().query("")
        soup = super().parse(html)
        group = soup.select(f"{html_id} option")
        return {i.get("value"): i.text for i in group}

    async def categories(self):
        return await self.get_options("#catgroup")

    async def subcategories(self):
        pass

    async def regions(self):
        return await self.get_options("#searcharea_expanded")
