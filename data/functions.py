import cv2
import easyocr
import requests
import asyncio
from bs4 import BeautifulSoup
from PIL import Image
from googlesearch import search
from googletrans import Translator


# Извлечение текста с изображения
async def text_extract(image):
    image = cv2.imread(image)
    text = easyocr.Reader(["ru", "en"], gpu=True).readtext(image, detail=0, paragraph=True)
    return "\n".join(text)


SUPPORTED_LANGUAGES = ["Английский", "Русский"]

language_codes = {
    "Русский": "ru",
    "Английский": "en"
}

translator = Translator()


# Перевод текста с исходного языка в нужный
async def translate_text(text, src_lang, dest_lang):
    return translator.translate(text, src=language_codes[src_lang], dest=language_codes[dest_lang]).text


# Запрос в Google
async def google_query(query):
    return [site for site in search(query, tld="co.in", num=3, stop=3, pause=2)]


async def getdata(url):
    r = requests.get(url)
    return r.text


async def get_images_url(url):
    htmldata = await getdata(url)
    soup = BeautifulSoup(htmldata, 'html.parser')
    items = []
    for item in soup.find_all('img'):
        if "tasks" in item["src"]:
            items.append(item['src'][2:])
    return items
