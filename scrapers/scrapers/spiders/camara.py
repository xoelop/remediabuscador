import re
import os
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import scrapy
from dotenv import load_dotenv
from scrapy.shell import inspect_response

load_dotenv()

if proxy := os.getenv("LUMINATI_PROXY_PER_IP_spain_1"):
    meta = {"proxy": proxy}
else:
    meta = {}


class CamaraSpider(scrapy.Spider):
    name = "camara"
    # start_urls = [
    #     "http://directorio.camaras.org/index.php?pagina=1&registros=0&offset=0&cocin=&impexp=E&anno=21&tramo=00&empresa=&producto=TA&codprod=&areanacional=PR&codareanac=&areainternac=PS&codareainter="
    # ]
    # not needed because we do start_requests
    
    # wait time 1 second
    handle_httpstatus_list = [401]


    custom_settings = {
        "HTTPCACHE_ENABLED": True,
        "HTTPCACHE_DIR": "httpcache",
        "HTTPCACHE_ALWAYS_STORE": True,  # TODO remove to get new data
        "HTTPCACHE_POLICY": "scrapers.scrapers.middlewares.CachePolicy",
        # 'DOWNLOAD_DELAY': 1
    }

    def start_requests(self):
        for page in range(1, 5):
            for tramo in ['01', '02', '03']:
                for producto in [f'{n:0>2}' for n in range(99)]:
                    url = f"http://directorio.camaras.org/index.php?pagina={page}&registros=0&offset=0&cocin=&impexp=E&anno=21&tramo={tramo}&empresa=&producto=TA&codprod={producto}&areanacional=PR&codareanac=&areainternac=PS&codareainter="
                    yield scrapy.Request(url=url, callback=self.parse, meta=meta)

    def parse(self, response):
        table = response.css("table.modTb.type2")[0]
        rows = table.css("tbody tr")
        for row in rows:
            columns = row.css("td")
            relative_url = columns[0].css("a::attr(href)").get()
            parts = re.findall("'.*?'", relative_url)
            nif,anno,impexp,tramo,iv = [p[1:-1] for p in parts]
            url = "http://directorio.camaras.org/verempresa.php?nif="+nif+"&anno="+anno+"&impexp="+impexp+"&tramo="+tramo+"&iv="+iv
            # relative_url is relative, and we need to pass the full url to the request. We can do that with the response.urljoin method
            yield scrapy.Request(
                url=url,
                callback=self.parse_mediador,
                meta=meta,
            )


    def parse_mediador(self, response):
        if response.status == 401:
            print('asdf')
        ullis_1_lis = response.css('.ullis')[0].css('li')
        address_1 = ullis_1_lis[0].css('::text').get()
        address_2 = ullis_1_lis[1].css('::text').get()
        telefono = ullis_1_lis[2].css('::text').get()
        
        ullis_4_lis = response.css('.ullis')[3].css('li')
        web = ullis_4_lis[1].css('a::attr(href)').get()
        email = ullis_4_lis[2].css('::text').get()
        
        data = {
            'address_1': address_1,
            'address_2': address_2,
            'telefono': telefono,
            'web': web,
            'email': email,
            'camaraURL': response.url
        }
        
        yield data

        # inspect_response(response, self)
        