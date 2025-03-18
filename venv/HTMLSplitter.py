import re

def split(html_text):
    # Регулярное выражение для поиска HTML-тегов
    tags_split = re.split(r'(</?[^>]+>)', html_text)
    # Удаляем пустые строки и возвращаем результат с новой строкой для каждого тега
    return "\n".join(tag.strip() for tag in tags_split if tag.strip())

def splitButStupid(text):
    res = []
    start = 0
    started = False
    for i in range(len(text)):
        if text[i] == '<' and not started:
            start = i
            started = True
            continue
        if text[i] == '<':
            started = False
            res.append(text[start:i])
            continue
    return res
