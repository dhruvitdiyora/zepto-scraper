import json
import time
import orjson
import urllib3
import asyncio
import datetime
import logging
from collections.abc import Iterator
from urllib3 import BaseHTTPResponse
from utils import try_extract, Listing, queries,  get_auth


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def get_response(query:str,location:str,auth:dict)-> BaseHTTPResponse:
    """"getting response from backend api for a given query and response"""
    logger.debug("Getting response")
    auth["user-agent"] = "Mozilla/5.0(Linux; U; Android 2.2; en-gb; LG-P500 Build/FRF91) AppleWebKit/533.0 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1"
    auth["storeId"] = location
    auth["store_etas"] = """{"""+location+""":0}"""
    auth["store_id"] = location
    auth["store_ids"] = location
    payload = orjson.dumps({"query": query, "pageNumber": 0, "userSessionId": auth["session_id"]})
    session = urllib3.PoolManager()
    resp = session.request("POST", "https://api.zeptonow.com/api/v3/search", headers=auth, body=payload)
    return resp


def extract_data(data:dict,query:str,store_id:str,loc:str)->Iterator[dict]:
    """extract data from response that is passed in the form of a dictionary"""
    logger.debug("Extracting data")
    for grid in data["layout"][1:-1]:
        for item in grid["data"]["resolver"]["data"]["items"]:
            product = item["productResponse"]
            mrp = int(try_extract(product,"mrp",0))//100
            price = int(try_extract(product,"sellingPrice",0))//100
            unit = try_extract(product["productVariant"],"weightInGms",0)
            name = try_extract(product["product"],"name","None")
            brand = try_extract(product["product"],"brand","None")
            try:
                cat = product["l3CategoriesDetail"][0]["name"]
            except TypeError:
                cat = "None"
            if product["meta"]["tags"][0]["type"]=="SPONSORED":
                ad = True
            else:
                ad = False
            rank = try_extract(item,"position",-1)
            dt = datetime.datetime.now()
            dt = datetime.datetime.strptime(str(dt).split(".")[0],"%Y-%m-%d %H:%M:%S")
            curr = Listing(
                platform="zepto",
                timestamp= dt,
                search_term = query,
                store_id=store_id,
                location = loc,
                mrp=mrp,
                price=price,
                unit=unit,
                brand=brand,
                name=name,
                cat=cat,
                ad=ad,
                rank=rank
            )
            yield curr.model_dump()

def scrape_zepto():
    """create new session and scrape for queries and location given in utils.constants.py"""
    headers = asyncio.run(get_auth(url="https://www.zeptonow.com/search?query=idli+rava",
                            api_term="api/v3/search",
                            request_method="POST"))
    logger.info("Initialized zepto scraper")
    logger.info(headers)

    logger.debug('Headers in place')
    store_id = 'fa5e892d-65d7-4da6-9bde-e1f22deb7b6f'
    locality = 'surat'
    for query in queries:
        items = []
        resp = get_response(query,store_id,headers)
        data = json.loads(resp.data)
        for item in extract_data(data,query,store_id,locality):
            items.append(item)
        time.sleep(0.5)
        logger.debug(f"""Recieved listings for {query} in {locality}""")
        yield items

if __name__ == '__main__':
    for item in scrape_zepto():
        for listing in item:
            print(listing)