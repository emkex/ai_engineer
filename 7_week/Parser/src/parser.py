import asyncio
import json
import re

import aiohttp
import fake_useragent
from bs4 import BeautifulSoup as BS
from playwright.async_api import async_playwright
from config import logger
from Interfaces import DatabaseStorage, MessageBroker

# Паттерн URL статей бензинги: /category/subcategory/YY/MM/articleID/slug
ARTICLE_URL_RE = re.compile(r'benzinga\.com/[a-z-]+/[a-z-]+/\d{2}/\d{2}/\d+/')


class Parser:
    def __init__(self, *, url, message_broker: MessageBroker, database_storage: DatabaseStorage):
        self.url = url
        self.news_refs = []
        self.user_agent = fake_useragent.UserAgent().random
        self.headers = {'user-agent': self.user_agent}
        self.message_broker = message_broker
        self.database_storage = database_storage

    async def run(self, delay_time):
        try:
            await self.get_articles_references()
            await self.parse_articles()
            await asyncio.sleep(delay_time)
        except Exception as error:
            logger.error(error)

    async def get_articles_references(self):
        """
        Используем Playwright headless чтобы:
        - дождаться загрузки JS-контента
        - прокрутить страницу и подгрузить ленивые статьи
        """
        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.set_extra_http_headers(self.headers)

                await page.goto(self.url, wait_until='domcontentloaded', timeout=30000)

                # Прокручиваем страницу вниз 4 раза — подгружаем lazy-контент
                for _ in range(4):
                    await page.evaluate('window.scrollBy(0, 1500)')
                    await asyncio.sleep(1.5)

                # Извлекаем все ссылки на статьи через JS прямо в браузере
                raw_links = await page.evaluate('''() => {
                    const pattern = /benzinga\\.com\\/[a-z-]+\\/[a-z-]+\\/\\d{2}\\/\\d{2}\\/\\d+\\//;
                    const seen = new Set();
                    const results = [];
                    document.querySelectorAll('a[href]').forEach(a => {
                        const href = a.href;
                        if (pattern.test(href) && !href.includes('?') && !seen.has(href)) {
                            seen.add(href);
                            results.push(href);
                        }
                    });
                    return results;
                }''')

                await browser.close()

            for href in raw_links:
                if not await self.database_storage.find_news(href):
                    self.news_refs.append(href)

            logger.info(f"Found {len(self.news_refs)} new articles")
        except Exception as error:
            logger.error(f"Failed main page parsing: {error}")

    async def parse_articles(self):
        tasks = [self._parse_article(ref=ref) for ref in self.news_refs]
        self.news_refs.clear()
        return await asyncio.gather(*tasks)

    async def _parse_article(self, ref):
        """
        Статьи серверно рендерятся — aiohttp + BeautifulSoup достаточно,
        playwright здесь был бы избыточен.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url=ref, headers=self.headers) as response:
                    response.raise_for_status()
                    html = await response.text()

            article = BS(html, 'html.parser')
            title_el = article.select_one('.article-title')
            body_el = article.select_one('#article-body')

            if not title_el or not body_el:
                logger.warning(f"Missing title or body, skipping: {ref}")
                return None

            title = title_el.text.strip()
            body = body_el.text.strip()

            self.message_broker.send(json.dumps({"title": title, "body": body}))
            logger.info(f"Sent to rabbit: {ref}")

            await self.database_storage.save({"reference": ref, "title": title, "body": body})
            logger.info(f"Saved in mongo: {ref}")

            return title, body
        except Exception as error:
            logger.error(f"Failed to parse article {ref}: {error}")
