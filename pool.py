import logging
from queue import SimpleQueue
from spider import get_proxies_from_xicidaili, get_proxies_from_sslproxies, get_proxies_from_hua
from judge import ProxyAdjudicator
from util import logger


class ProxyPool():
  def __init__(self):
    self.raw_proxies = SimpleQueue()
    self.proxy_set = set()

    self.pc = ProxyCollector()
    self.pa = ProxyAdjudicator()

  def build_proxy_set(self):
    self.pc.call_spiders(self.raw_proxies)
    self.pa.judge_proxies_quality(self.raw_proxies, self.proxy_set)

  def add_proxy_set(self):
    temp_set = set()
    self.pc.call_spiders(self.raw_proxies)
    self.pa.judge_proxies_quality(self.raw_proxies, temp_set)
    self.proxy_set = self.proxy_set.update(temp_set)
    logger.critical(f"Sum Available Proxies: {len(self.proxy_set)}")

  def rejudge_proxy_set(self):
    self.pa.rejudge(self.proxy_set)


class ProxyCollector():

  def call_spiders(self, raw_proxies):
    logger.critical("Call Spiders")

    logger.critical("Get Proxies From Hua")
    get_proxies_from_hua(raw_proxies)

    logger.critical("Get Proxies From XiCi")
    get_proxies_from_xicidaili(raw_proxies)

    logger.critical("Get Proxies From SSLProxies")
    get_proxies_from_sslproxies(raw_proxies)