from time import sleep
import threading
from datetime import datetime
from queue import SimpleQueue
import aiohttp
import asyncio
from util import logger


class ProxyAdjudicator():
  def __init__(self):

    self.count = 0

  async def _get_judge_result(self, proxy):
    start_t = datetime.now()
    try:
      res = await self.session.get(
          f'http://api.bilibili.com/x/relation/stat?vmid=7', proxy=proxy, timeout=9)
      if res.status != 200:
        return (res.status, 9.9)
    except Exception as e:
      return ("???", 9.9)
    delta_t = datetime.now() - start_t
    return (res.status, round(delta_t.total_seconds(), 1))

  async def _judge_ip(self, proxy):
    code, t = await self._get_judge_result(proxy)
    if code == 200:
      state = '\033[1;32m PASS \033[0m'
      if t > 1.5:
        state = '\033[1;33m SLOW \033[0m'
        flag = False
      else:
        flag = True
    else:
      state = '\033[1;31m FAIL \033[0m'
      flag = False
    logger.info(f'[{state}] ({code}) {t}s {proxy}')
    return flag

  async def _judge_task(self, judge_queue: SimpleQueue, result_set: set):
    while not judge_queue.empty():
      self.count += 1
      proxy = judge_queue.get()
      proxy = f"{proxy['protocol']}://{proxy['address']}"
      is_pass = await self._judge_ip(proxy)
      if is_pass:
        result_set.add(proxy)

  def _start_judge_task(self, judge_queue: SimpleQueue, result_set: set):
    if not judge_queue.empty():
      concurrence = 32
      loop = asyncio.new_event_loop()
      asyncio.set_event_loop(loop)
      self.session = aiohttp.ClientSession()
      tasks = [self._judge_task(judge_queue, result_set)
               for i in range(concurrence)]
      loop.run_until_complete(asyncio.wait(tasks))
      logger.critical(f"Totail Proxies: {self.count}")
      logger.critical(f"Available Proxies: {len(result_set)}")
      loop.run_until_complete(asyncio.wait([self.session.close()]))
      loop.close()

  async def _rejudge_proxy(self, proxy, remove_set):
    code, time = await self._get_judge_result(proxy)
    if code != 200 or time > 5:
      remove_set.add(proxy)
      logger.info(f"[ \033[1;31m DELETE \033[0m ] {proxy}")
    else:
      logger.info(f"[ \033[1;32m REMAIN \033[0m ] {proxy}")

  async def _rejudge(self, result_set: set):
    remove_set = set()
    for proxy in proxy_set:
      _rejudge_proxy(proxy, remove_set)
    proxy_set.difference_update(remove_set)
    logger.critical(f"Available Proxies: {len(proxy_set)}")

  def rejudge(self, proxy_set: set):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    self.session = aiohttp.ClientSession()
    loop.run_until_complete(asyncio.wait([self._rejudge(proxy_set)]))
    loop.run_until_complete(asyncio.wait([self.session.close()]))
    loop.close()

  def judge_proxies_quality(self, raw_proxies, proxy_set):
    logger.critical("Judge Proxies Quality")
    self._start_judge_task(raw_proxies, proxy_set)