#!/usr/bin/env python3.8
import configparser
import json
import logging
import os
import re
import sys
import traceback
from datetime import datetime
from pathlib import PurePath, Path

from mega import Mega
from playwright.sync_api import sync_playwright
from random_user_agent.params import SoftwareName, OperatingSystem
from random_user_agent.user_agent import UserAgent

software_names = [SoftwareName.ANDROID.value]
operating_systems = [OperatingSystem.ANDROID.value]
user_agent_rotator = UserAgent(software_names=software_names, operating_systems=operating_systems, limit=10)
user_agent = user_agent_rotator.get_random_user_agent()
print(user_agent)
config = configparser.ConfigParser()
config.read("config.ini")
pop_up_extension = "./Extensions/bkkbcggnhapdmkeljlodobbkopceiche/5.3.0_0"
ad_block_extension = "./Extensions/kgddnoifhgfdhcpbkkjdgokfnkkmdcen/1.0.4_0"
user_temp = "./tmp/user-data"
storage_path = config["Config"]["storage"]

mega = Mega()
mg = mega.login()


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
to_search = ["eggs priority", "blood c", "tokyo ghoul", "mirai nikki", "Boku No Hero", "Vinland Saga", "Tokyo Revenger"]


def already_downloaded(abs_path: PurePath, file_name: str):
    for file in os.listdir(abs_path):
        if file_name in file:
            return True


def result(page_driver):
    result_search = page_driver.locator(".List-Animes li")
    for x in range(result_search.count()):
        anime = result_search.nth(x)
        href_element = anime.locator("a")
        is_ova = True if "OVA" in href_element.locator("figure > span").text_content() or \
                         "Pelicula" in href_element.locator("figure > span").text_content() else False
        anime_title = href_element.locator(".Title").text_content()
        logger.info(anime_title)
        result_page = context.new_page()
        result_page.goto(f'{scrapper_vars["web"]}{href_element.get_attribute("href")}')
        episodes = result_page.locator(".List-Episodes div ul li")
        logger.info(episodes)
        for e in range(episodes.count()):
            link_episode = episodes.nth(e).locator("a").get_attribute("href")
            logger.info(link_episode)
            if "#" != link_episode:
                result_page.goto(f'{scrapper_vars["web"]}{episodes.nth(e).locator("a").get_attribute("href")}')
                script_tags = result_page.locator("script")
                mega_link = None
                for s in range(script_tags.count()):
                    if "anime_id" in script_tags.nth(s).text_content() and "episode_id" in script_tags.nth(
                            s).text_content():
                        raw_script = script_tags.nth(s).text_content()
                        get_json_data = re.search("(?<=videos =).*", raw_script, re.IGNORECASE).group().replace(";", "")
                        parse_json = json.loads(get_json_data)
                        get_mega_data = [x for x in parse_json['SUB'] if x["server"] == "mega"][0]
                        mega_link = get_mega_data["url"]
                logger.info(mega_link)
                if mega_link:
                    episode_element = result_page.locator(".Title-Episode").text_content()
                    episode = re.search("(\d){1,3}", episode_element).group()
                    file_name = anime_title if is_ova else f'{anime_title} episode {episode}'
                    abs_path = PurePath(storage_path, "Anime", "Movie" if is_ova else "TV", anime_title)
                    Path(abs_path).mkdir(parents=True, exist_ok=True)
                    try:
                        logger.info("Starting download....")
                        if not already_downloaded(abs_path, file_name):
                            r = mg.download_url(mega_link, abs_path.as_posix())
                            mega_file_id = r.name.split(".")[0]
                            rename(abs_path, mega_file_id, file_name)
                            logger.info(f"Download completed:{file_name}")
                    except:
                        logger_download_fails.error(traceback.print_exc())
                        pass
                result_page.go_back()
        result_page.close()


with sync_playwright() as driver:
    logger.info("Start scrapper")
    scrapper_vars = config["Scrapper"]
    try:
        context = driver.chromium.launch_persistent_context(
            user_agent=user_agent,
            user_data_dir=user_temp,
            headless=True,
            args=[
                f'--disable-extensions-except={pop_up_extension},{ad_block_extension}',
                f'--load-extension={pop_up_extension},{ad_block_extension}',
            ],
            slow_mo=5000
        )
    except:
        logger.error(traceback.print_exc())
        raise "COULDN'T CREATE CONTEXT"
    try:
        page = context.new_page()
        page.goto(scrapper_vars["web"] + "/browse")
        for c in context.pages:
            if "/browse" not in c.url:
                c.close()
        for i in to_search:
            page.click("[for=Input-Search]")
            page.fill("#Input-Search", i)
            page.keyboard.press("Enter")
            logger.info("Búsqueda realizada correctamente")
            result(page)
        page.goto(scrapper_vars["web"] + "/browse")
        result(page)

    except:
        logger.error(traceback.print_exc())
        pass
    context.close()
