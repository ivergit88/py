import asyncio
import concurrent.futures
import multiprocessing
import threading

import aiohttp
import requests

async def async_fetch(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url) as resp:
        res = await resp.text()
        return res

async def async_requests(urls: list[str]) -> list[str]:
    tasks_list = []
    for url in urls:
        session = aiohttp.ClientSession()
        tasks_list.append(async_fetch(session, url))
    iter_res = await asyncio.gather(*tasks_list)
    return list(iter_res)

collected_texts: list[str] = []

def sync_fetch(session: requests.Session, url: str) -> str:
    with session.get(url) as resp:
        res = resp.text
        collected_texts.append(res)
        return res

def threaded_requests(urls: list[str]) -> list[str]:
    args_both = []
    with requests.Session() as session:
        for url in urls:
            args_both.append((session, url))
    with multiprocessing.Pool() as pool:
        result = pool.starmap(sync_fetch, args_both)
    return result