#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WordleHelper - Помощник для игры в "5 слов"

Описание:
  Скрипт помогает отгадывать слова в игре "5 слов", используя заданные известные и неизвестные буквы,
  а также буквы, которые точно отсутствуют в слове. Фильтрует только существительные (по суффиксам).

Использование:
  python3 main.py [options]
  Используйте python3 main.py --help для получения информации о скрипте.

Опции:
  --known <pattern>      Буквы на известных позициях. Пример: м_тр_
  --unknown <letters>    Буквы, присутствующие в слове, но позиция неизвестна.
  --excluded <letters>   Буквы, отсутствующие в слове.

Автор: Maksim Borzov
Версия: 1.0.1
"""

import re
import argparse

class WordleHelper:
    def __init__(self, dictionary_path='dictionary.txt'):
        # Инициализация объекта с прочтением слов длиной в 5 букв из файла
        with open(dictionary_path, 'r', encoding='utf-8') as file:
            self.words = [word.strip().lower() for word in file if len(word.strip()) == 5 and self._is_likely_noun(word.strip().lower())]

    def _is_likely_noun(self, word):
        # Проверка наличия окончаний, характерных для существительных
        common_noun_endings = (
            'а', 'я', 'о', 'е', 'ё', 'мя', 'ь', 'ий', 'ы', 'и',
            'ей', 'ия', 'ий', 'ий', 'ей', 'й', 'е', 'ё', 'я'
        )
        return word.endswith(common_noun_endings)
    
    def find_words(self, known='', unknown='', excluded=''):
        # Приведение всех входных параметров к нижнему регистру
        known = known.lower()
        unknown = unknown.lower()
        excluded = excluded.lower()

        # Генерация шаблона по известным позициям букв
        pattern = self._generate_pattern(known)
        # Фильтрация слов по шаблону
        filtered_words = self._filter_words_by_pattern(pattern)

        # Фильтрация слов по включенным буквам
        if unknown:
            filtered_words = self._filter_words_by_inclusion(filtered_words, unknown)

        # Фильтрация слов по исключенным буквам
        if excluded:
            filtered_words = self._filter_words_by_exclusion(filtered_words, excluded)

        return filtered_words

    def _generate_pattern(self, known):
        # Замена нижних подчеркиваний на точки для создания регулярного выражения
        return known.replace('_', '.')

    def _filter_words_by_pattern(self, pattern):
        # Создание и применение регулярного выражения на список слов
        regex = re.compile(f'^{pattern}$')
        return [word for word in self.words if regex.match(word)]

    def _filter_words_by_inclusion(self, words, unknown):
        # Фильтрация слов, содержащих все заданные буквы
        return [word for word in words if all(letter in word for letter in unknown)]

    def _filter_words_by_exclusion(self, words, excluded):
        # Фильтрация слов, не содержащих ни одной из указанных букв
        return [word for word in words if all(letter not in word for letter in excluded)]

if __name__ == '__main__':
    # Обработчик аргументов командной строки
    parser = argparse.ArgumentParser(description="Помощник для игры в '5 слов'.",
                                     usage="python3 main.py [options] --help для получения информации о скрипте")
    parser.add_argument('--known', type=str, default='_____', help='Буквы на известных позициях. Пример: м_тр_')
    parser.add_argument('--unknown', type=str, default='', help='Буквы, присутствующие в слове, но позиция неизвестна.')
    parser.add_argument('--excluded', type=str, default='', help='Буквы, отсутствующие в слове.')

    args = parser.parse_args()

    helper = WordleHelper()

    results = helper.find_words(args.known, args.unknown, args.excluded)
    
    # Вывод подходящих слов или сообщение об их отсутствии
    if results:
        print("Подходящие слова:")
        for word in results:
            print(word)
    else:
        print("Подходящих слов не найдено.")