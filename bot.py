import asyncio
import logging
import sys
from os import getenv

from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import hbold

import requests
from bs4 import BeautifulSoup
import undetected_chromedriver
import time
import json

from dotenv import load_dotenv
load_dotenv()

# Bot token can be obtained via https://t.me/BotFather
TOKEN = getenv("BOT_TOKEN")

# All handlers should be attached to the Router (or Dispatcher)
dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer("Привет сукин сын!\nДанный бот показывает цены на книги в разных магазинах.\nНе дай боярам тебя обмануть, покупай только там, где дешево!\n\nСукин сын собирает цены с:\n1. Читай-города\n2. Wildberries\n3. Лабиринт\n\nИнструкция:\nПросто пиши название книги, а сукин сын все сделает!\n")


@dp.message()
async def book_name_handler(message: types.Message) -> None:
    try:
        answer = parse_chitai_gorod_book(book_name=message.text)
        answer += parse_wildberries_book(book_name=message.text)
        answer += parse_labirint_book(book_name=message.text)
        await message.reply(
                text=answer, 
                parse_mode="html"
            )
    except Exception as ex:
        logging.log(level=logging.ERROR, msg=ex)
        await message.answer("Господи прости меня грешного, перегрелся я что-то")


def parse_chitai_gorod_book(book_name: str, limit: int = 5) -> str:
    books_result = ["<b>Читай город:</b>"]

    base_url = f'https://www.chitai-gorod.ru'
    response = requests.get(f"{base_url}/search?phrase={book_name}").text
    soup = BeautifulSoup(response, "lxml")
    books = soup.find_all("article", class_="product-card product-card product")
    links = soup.find_all("a", class_="product-card__title")
    authors = soup.find_all("div", class_="product-title__author")

    i: int = 0
    for book in books:
        if i == limit:
            break
        link = f'{base_url}{links[i].get("href")}'
        name = book["data-chg-product-name"]
        price = book["data-chg-product-price"]
        author = authors[i].text.replace("\n", "").strip()
        books_result.append(f"<a href='{link}'>Ссылка на книгу</a>\n<b>Книга:</b> {name}\n<b>Цена:</b> {price}\n<b>Автор:</b> {author}\n")
        i += 1

    return "\n".join(books_result)


def parse_wildberries_book(book_name: str, limit: int = 5) -> str:
    books_result = ["\n\n\n<b>Wildberries:</b>"]

    response = requests.get(f"https://search.wb.ru/exactmatch/ru/common/v4/search?TestGroup=no_test&TestID=no_test&appType=1&curr=rub&dest=-1257786&query={book_name}&resultset=catalog&sort=popular&spp=29&suppressSpellcheck=false")

    json_data = response.text
    data = json.loads(json_data)

    # Get info about product
    if "data" in data and "products" in data["data"]:
        products = data["data"]["products"]

        for product in products[:limit]:
            id = product.get("id")
            name = product.get("name")
            sale_price = str(product.get("salePriceU"))

            if name and sale_price:
                books_result.append(f'<a href="https://www.wildberries.ru/catalog/{id}/detail.aspx">Ссылка на книгу</a>\n<b>Книга:</b> {name}\n<b>Цена:</b> {sale_price[:-2]}\n')

    return '\n'.join(books_result)


def parse_labirint_book(book_name: str, limit: int = 5) -> str:
    books_result = ["\n\n\n<b>Лабиринт:</b>"]

    base_url = f'https://www.labirint.ru'
    response = requests.get(f"{base_url}/search/{book_name}").text
    soup = BeautifulSoup(response, "lxml")
    books = soup.find_all("div", class_="product-card need-watch")
    authors = soup.find_all("div", class_="product-card__author")

    i: int = 0
    for book in books:
        if i == limit:
            break

        id = book["data-product-id"]
        name = book["data-name"]
        price = book["data-discount-price"]
        author = authors[i].text
        books_result.append(f"<a href='{base_url}/books/{id}'>Ссылка на книгу</a>\n<b>Книга:</b> {name}\n<b>Цена:</b> {price}\n<b>Автор:</b> {author}\n")
        i += 1

    return '\n'.join(books_result)


async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
