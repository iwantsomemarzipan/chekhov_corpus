import sqlite3
import stanza

nlp = stanza.Pipeline('ru', processors='tokenize,lemma')

path_to_db = './instance/corpus.db'

conn = sqlite3.connect(path_to_db)
cursor = conn.cursor()

def search_sequence(query):
    """
    Производит поиск предложений в БД в соответствии
    с токенами введёной последовательности длиной от 1 до 3 и типом запроса 
    """
    tokens = query.split()
    if len(tokens) == 0 or len(tokens) > 3:
        raise ValueError("Запрос должен содержать от 1 до 3 токенов")
    
    # SQL-запрос для поиска последовательности токенов
    base_query = '''
        SELECT DISTINCT s.original_sentence, s.work_title, s.source
        FROM sentences s
    '''
    joins = []
    conditions = []
    params = []

    # Проходим по каждому токену и определяем его тип
    for i, token in enumerate(tokens):
        alias = f't{i}'  # Создаем алиасы на случай повторных присоединений таблицы
        joins.append(f'JOIN tokens {alias} ON s.id = {alias}.sentence_id')

        if token.isupper():
            # Если токен — это POS-тег
            conditions.append(f'{alias}.pos = ?')
            params.append(token)

        elif token.startswith('"') and token.endswith('"'):
            # Если токен в кавычках — конкретная словоформа
            token = token[1:-1]
            conditions.append(f'{alias}.token = ?')
            params.append(token)

        elif '+' in token:
            # Если токен содержит словоформу и POS-тег
            token, pos = token.split('+')
            conditions.append(f'{alias}.token = ? AND {alias}.pos = ?')
            params.append(token)
            params.append(pos)

        else:
            # Иначе поиск по лемме
            doc = nlp(token)
            lemma = [word.lemma for t in doc.sentences for word in t.words]
            lemma = ''.join(lemma)
            conditions.append(f'{alias}.lemma = ?')
            params.append(lemma)

    # Убедимся, что токены идут друг за другом в предложении
    for i in range(len(tokens) - 1):
        conditions.append(f't{i}.id + 1 = t{i+1}.id')

    # Строим итоговый SQL-запрос
    query = base_query + ' ' + ' '.join(joins) + ' WHERE ' + ' AND '.join(conditions)
    
    cursor.execute(query, tuple(params))
    return cursor.fetchall()

def format_results(results):
    """
    Выдаёт результат поиска
    """
    if not results:
        print("Не найдено предложений, соответствующих запросу.")
    else:
        for original_sentence, work_title, source in results:
            print(f"Предложение: {original_sentence}\nРассказ: {work_title}\nИнтернет-источник: {source}\n")

def search(query):
    """
    Основная функция поиска
    """
    results = search_sequence(query)
    format_results(results)
