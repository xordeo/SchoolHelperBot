import cv2
import easyocr
from PIL import Image

from googletrans import Translator


# Извлечение текста с изображения
def text_extract(image):
    image = cv2.imread(image)
    text = easyocr.Reader(["ru", "en"]).readtext(image, detail=0, paragraph=True)
    return "\n".join(text)


language_codes = {
    "Русский": "ru",
    "Английский": "en"
}

translator = Translator()


# Перевод текста с исходного языка в нужный
def translate_text(text, src_lang, dest_lang):
    return translator.translate(text, src=language_codes[src_lang], dest=language_codes[dest_lang]).text
