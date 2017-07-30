from text_processing.mystem.text_processor import TextProcessor

questions = ['Запись в детский сад', 'Как добавиться в чат', 'Какие кафе есть в Иннополисе?',
             'Где автобус?', 'Отдел полиции', 'Пожар', 'Как вызвать врача', 'Течёт кран', 'Как вызвать полицию',
             'Где полиция', 'Номер участкового', 'Где можно поесть?']

if __name__ == '__main__':
    with TextProcessor() as nlp:
        in_text = input("Input smth if u want to lemmatize predefined questions, otherwise type Enter: ")

        if in_text != '':
            keywords = [nlp.extract_keywords(q) for q in questions]

            with open('test_result.txt', mode='w', encoding='utf-8') as f:
                for i, q in enumerate(questions):
                    f.write('%s: %s\n' % (q, str(keywords[i])))
        else:
            while in_text != 'exit':
                in_text = input('> ')
                print('> %s\n' % str(nlp.get_tokens(in_text, include_words_info=True)))
                print('> %s\n' % str(nlp.extract_keywords(in_text, include_partial_keywords=False)))

# if __name__ == '__main__':
#     tp = TextProcessor()
#
#     while True:
#         print(tp.get_spelling_variants(input('> ')))
