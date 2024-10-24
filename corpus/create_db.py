import re
import nltk
import sqlite3
import stanza
from metadata import author, titles

nlp = stanza.Pipeline('ru', processors='tokenize,lemma,pos')

conn = sqlite3.connect('corpus.db')
cursor = conn.cursor()

# Создание таблицы для предложений
cursor.execute('''
    CREATE TABLE sentences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_sentence TEXT,
        clean_sentence TEXT,
        work_title TEXT,
        author TEXT,
        source TEXT
    )
''')

conn.commit()

# Создание таблицы для токенов
cursor.execute('''
    CREATE TABLE tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sentence_id INTEGER,
        token TEXT,
        lemma TEXT,
        pos TEXT,
        FOREIGN KEY (sentence_id) REFERENCES sentences (id)
    )
''')

conn.commit()

# Создание индексов
cursor.execute('CREATE INDEX idx_token ON tokens (token)')
cursor.execute('CREATE INDEX idx_lemma ON tokens (lemma)')
cursor.execute('CREATE INDEX idx_pos ON tokens (pos)')
cursor.execute('CREATE INDEX idx_lemma_pos ON tokens (lemma, pos)')
conn.commit()

def split_into_sentences(text):
    """
    Разделяет текст на предложения
    """
    sentences = nltk.sent_tokenize(text, language='russian')
    return sentences

def clean_text(text):
    """
    Удаляет нетекстовые элементы и обрабатывает дефисы.
    Оставляет буквы (русские и латинские) и цифры.
    """
    # Сначала заменим все нетекстовые символы, кроме букв, цифр и пробелов
    cleaned_text = re.sub(r'[^a-zA-Zа-яА-ЯёЁ0-9\s-]', '', text)
    
    # Разбиваем слова по дефисам, оставляя их как отдельные слова
    split_text = re.sub(r'(\w+)-(\w+)', r'\1 \2', cleaned_text)
    
    return split_text

def save_morph(sentence, sentence_id):
    """
    Проводит морфологический анализ и вставляет результаты в таблицу БД
    """
    doc = nlp(sentence)
    
    for sent in doc.sentences:
        for token in sent.words:
            cursor.execute('''
                INSERT INTO tokens (sentence_id, token, lemma, pos)
                VALUES (?, ?, ?, ?)
            ''', (sentence_id, token.text, token.lemma, token.upos))

    conn.commit()

def save_sentences_and_morph(txt_file, title, author, url):
    """
    Вставяет предложения в таблицу БД
    """    
    with open(txt_file, 'r', encoding='utf-8') as file:
        text = file.read()

    sentences = split_into_sentences(text)
    
    cleaned_sentences = [clean_text(sentence) for sentence in sentences]

    for sentence, clean_sent in zip(sentences, cleaned_sentences):
        cursor.execute('''
            INSERT INTO sentences (
                original_sentence, clean_sentence, work_title, author, source
            )
            VALUES (?, ?, ?, ?, ?)
        ''', (sentence, clean_sent, title, author, url))

        sentence_id = cursor.lastrowid
        save_morph(clean_sent, sentence_id)

    conn.commit()

for title, url in titles.items():
    file_dir = f'./texts/{title}.txt'
    save_sentences_and_morph(file_dir, title, author, url)
