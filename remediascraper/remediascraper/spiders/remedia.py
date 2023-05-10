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


class RemediaSpider(scrapy.Spider):
    name = "remedia"
    allowed_domains = ["remediabuscador.mjusticia.gob.es"]
    # start_urls = [
    #     "https://remediabuscador.mjusticia.gob.es/remediabuscador/avanzarRetrocederRegistroMediador.action?paginacion.index=40&nombre=&especialidad=0&area="
    # ]
    # not needed because we do start_requests

    custom_settings = {
        "HTTPCACHE_ENABLED": True,
        "HTTPCACHE_DIR": "httpcache",
        "HTTPCACHE_ALWAYS_STORE": True,  # TODO remove to get new data
        "HTTPCACHE_POLICY": "remediascraper.remediascraper.middlewares.CachePolicy",
    }

    def start_requests(self):
        # total: 8159 results. 20 per page, so 408 pages in total
        for i in range(1, 409):
            url = f"https://remediabuscador.mjusticia.gob.es/remediabuscador/avanzarRetrocederRegistroMediador.action?paginacion.index={i}&nombre=&especialidad=0&area="
            yield scrapy.Request(url=url, callback=self.parse, meta=meta)

    def parse(self, response):
        table = response.css("table.tabla_datos")[0]
        rows = table.css("tbody tr")
        for row in rows:
            columns = row.css("td")
            relative_url = columns[0].css("a::attr(href)").get()
            # relative_url is relative, and we need to pass the full url to the request. We can do that with the response.urljoin method
            yield scrapy.Request(
                url=response.urljoin(relative_url),
                callback=self.parse_mediador,
                meta=meta,
            )

        # this approach would redirect us to page 1 after 40 pages or so
        # next_page_link = response.xpath("//ul[@id='resultados']//a[contains(text(), 'Siguiente')]")
        # if next_page_link:
        #     next_page_relative_url = next_page_link.attrib['href']
        #     next_page_full_url = response.urljoin(next_page_relative_url)
        #     yield scrapy.Request(url=next_page_full_url, callback=self.parse, meta=meta)
        # else:
        #     inspect_response(response, self)

    def parse_mediador(self, response):
        # inspect_response(response, self)
        paragraphs = response.css("div.detallePublicacion p")
        name = paragraphs[0].css("::text").getall()[-1][1:].strip()
        address = paragraphs[1].css("::text").getall()[-1][1:].strip()
        email = paragraphs[2].css("::text").getall()[-1][1:].strip()
        speciality = paragraphs[3].css("::text").getall()[-1][1:].strip()
        area = paragraphs[4].css("::text").getall()[-1][1:].strip()
        experience = paragraphs[5].css("::text").getall()[-1][1:].strip()
        mediador = {
            "name": name,
            "address": address,
            "email": email,
            "speciality": speciality,
            "area": area,
            "experience": experience,
            "mediador_link": response.urljoin(response.url),
        }
        yield mediador
