#!/usr/bin/env python3.8
import configparser
import logging
import os
import re
import sys
import traceback
from datetime import datetime
from pathlib import PurePath, Path

from mega import Mega
from playwright.sync_api import sync_playwright

config = configparser.ConfigParser()
config.read("config.ini")
pop_up_extension = "./Extensions/bkkbcggnhapdmkeljlodobbkopceiche/5.3.0_0"
ad_block_extension = "./Extensions/kgddnoifhgfdhcpbkkjdgokfnkkmdcen/1.0.4_0"
user_temp = "./tmp/user-data"
storage_path = config["Config"]["storage"]

mega = Mega()
mg = mega.login(config["Mega"]["email"], config["Mega"]["password"])


def setup_logger(name):
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    handler = logging.FileHandler(f'storage/{name}-{datetime.today().strftime("%Y-%m-%d")}.log', mode='w')
    handler.setFormatter(formatter)
    screen_handler = logging.StreamHandler(stream=sys.stdout)
    screen_handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.addHandler(screen_handler)
    return logger


def rename(path: PurePath, id: str, name: str):
    os.chdir(path)
    for file in os.listdir(path):
        if id in file:
            name = file.replace(id, name)
            os.rename(file, name)


logger = setup_logger('mega')
logger_download_fails = setup_logger("fails")
to_search = ["eggs priority",  "Tokyo Revenger"]


def result(page_driver):
    result_search = page_driver.locator(".ListAnimes.AX.Rows li")
    for x in range(result_search.count()):
        anime = result_search.nth(x)
        href_element = anime.locator("article > a")
        is_ova = True if "OVA" in href_element.locator("div > span").text_content() else False
        anime_title = href_element.locator(".Title").text_content()
        result_page = context.new_page()
        result_page.goto(f'{scrapper_vars["web"]}{href_element.get_attribute("href")}')
        episodes = result_page.locator("#episodeList li")
        for e in range(episodes.count()):
            link_episode = episodes.nth(e).locator("a").get_attribute("href")
            if "#" != link_episode:
                result_page.goto(f'{scrapper_vars["web"]}{episodes.nth(e).locator("a").get_attribute("href")}')
                mega_link = result_page.locator("a[href*=mega]").get_attribute("href")
                episode_element = result_page.locator("h2.SubTitle").text_content()
                episode = re.search("(\d){1,3}", episode_element).group()
                abs_path = PurePath(storage_path, "Anime", "Movie" if is_ova else "TV", anime_title)
                Path(abs_path).mkdir(parents=True, exist_ok=True)
                try:
                    logger.info("Starting download....")
                    # r = mg.download_url(mega_link, abs_path.as_posix())
                    # file_mime = r.name.split(".")[1]
                    # mega_file_id = r.name.split(".")[0]
                    file_name = anime_title if is_ova else f'{anime_title} episode {episode}'
                    # rename(abs_path, mega_file_id, file_name)
                    logger.info(f"Download completed:{file_name}")
                except:
                    logger_download_fails.error(traceback.print_exc())
                    pass
                result_page.go_back()
        result_page.close()


with sync_playwright() as driver:
    logger.info("Start scrapper")
    scrapper_vars = config["Scrapper"]
    context = driver.chromium.launch_persistent_context(
        user_data_dir=user_temp,
        headless=False,
        args=[
            f'--disable-extensions-except={pop_up_extension},{ad_block_extension}',
            f'--load-extension={pop_up_extension},{ad_block_extension}',
        ],
        slow_mo=5000
    )
    try:
        page = context.new_page()
        page.goto(scrapper_vars["web"] + "/browse")
        [blank, scrapping, extension] = context.pages
        extension.close()
        blank.close()
        for i in to_search:
            page.fill("#search-anime", i)
            page.keyboard.press("Enter")
            result(page)
        page.goto(scrapper_vars["web"] + "/browse")
        result(page)

    except:
        logger.error(traceback.print_exc())
        pass
    context.close()
