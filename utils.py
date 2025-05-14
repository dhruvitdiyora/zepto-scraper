from selenium_driverless import webdriver
from selenium_driverless.scripts.network_interceptor import NetworkInterceptor, InterceptedRequest
from pydantic import BaseModel,Field
import datetime

queries = [
    "idli rava",
    "bansi sooji",
    "poha medium avalakki",
    "thick poha",
]

class Listing(BaseModel):
    platform: str
    timestamp: datetime.datetime
    search_term: str
    store_id: str
    location: str
    mrp: int
    price: int
    unit: int
    brand: str
    name: str
    cat: str
    ad: bool
    rank: int

class Location(BaseModel):
    platform: str
    store_id: str
    locality: str
    longitude: float
    latitude: float

def try_extract(obj:dict,field:str,default):
    """try clause for extracting a field from response.json"""
    try:
        return obj[field]
    except KeyError or TypeError:
        return default
    
async def get_auth(url:str,api_term:str,request_method:str)->dict:
    """getting fresh headers for a search session"""
    auth = {}
    async def on_request(data: InterceptedRequest) -> None:
        """setting global variable auth with intercepted network request"""
        if api_term in data.request.url and data.request.method == request_method:
            nonlocal auth
            try:
                auth = data.request.headers
            except KeyError:
                print("no auth header found in request")
    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")  # Important for Docker
    options.add_argument("--disable-gpu")
    options.headless = True
    async with webdriver.Chrome(options=options) as driver:
        async with NetworkInterceptor(driver,on_request=on_request):
            await driver.get(url)
            await driver.sleep(0.5)
    return auth
