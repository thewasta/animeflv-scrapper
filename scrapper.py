#!/usr/bin/env python3.8
import configparser
import time
from mega import Mega
from playwright.sync_api import sync_playwright

config = configparser.ConfigParser()
config.read("config.ini")
pop_up_extension = "./Extensions/bkkbcggnhapdmkeljlodobbkopceiche/5.3.0_0"
ad_block_extension = "./Extensions/kgddnoifhgfdhcpbkkjdgokfnkkmdcen/1.0.4_0"
user_temp = "./tmp/user-data"
mega = Mega()
mg = mega.login(config["Mega"]["email"], config["Mega"]["password"])

with sync_playwright() as driver:
    scrapper_vars = config["Scrapper"]
    context = driver.chromium.launch_persistent_context(
        user_data_dir=user_temp,
        headless=False,
        args=[
            f'--disable-extensions-except={pop_up_extension},{ad_block_extension}',
            f'--load-extension={pop_up_extension},{ad_block_extension}',
        ],
        slow_mo=2500
    )
    page = context.new_page()
    page.goto(scrapper_vars["web"])
    [blank, scrapping, extension] = context.pages
    extension.close()
    blank.close()
    page.fill("#search-anime", "tokyo ghoul")
    page.keyboard.press("Enter")
    result_search = page.locator(".ListAnimes.AX.Rows li")
    for x in range(result_search.count()):
        anime = result_search.nth(x)
        href_element = anime.locator("article > a")
        is_ova = True if "OVA" in href_element.locator("div > span") else False
        result_page = context.new_page()
        result_page.goto(f'{scrapper_vars["web"]}{href_element.get_attribute("href")}')
        episodes = result_page.locator("#episodeList li")
        for e in range(episodes.count()):
            result_page.goto(f'{scrapper_vars["web"]}{episodes.nth(e).locator("a").get_attribute("href")}')
            mega_link = result_page.locator("a[href*=mega]").get_attribute("href")
            mg.download_url(mega_link, "./storage/")
        break
    print(result_search)
    time.sleep(10)
    context.close()
