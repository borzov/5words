#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WordleHelper - Помощник для игры в "5 слов"

Описание:
  Скрипт помогает отгадывать слова в игре "5 слов", используя заданные известные и неизвестные буквы,
  а также буквы, которые точно отсутствуют в слове.

Использование:
  python3 main.py [options]
  python3 main.py --interactive  # интерактивный режим
  Используйте python3 main.py --help для получения информации о скрипте.

Опции:
  --known <pattern>      Буквы на известных позициях. Пример: м_тр_
  --unknown <letters>    Буквы, присутствующие в слове, но позиция неизвестна.
  --excluded <letters>   Буквы, отсутствующие в слове.
  --limit <N>           Максимальное количество результатов (по умолчанию: все)
  --no-sort             Отключить сортировку по частотности
  --stats               Показать статистику по буквам
  --suggest             Предложить оптимальное следующее слово
  --interactive         Интерактивный режим с пошаговыми подсказками

Автор: Maksim Borzov
Версия: 2.0.0
"""

import re
import argparse
import sys
from collections import Counter, defaultdict
import random


class WordleHelperError(Exception):
    """Базовый класс для ошибок WordleHelper"""
    pass


class ValidationError(WordleHelperError):
    """Ошибка валидации входных данных"""
    pass


class WordleHelper:
    # Частоты букв в русском языке (приблизительные)
    LETTER_FREQUENCIES = {
        'о': 10.97, 'е': 8.45, 'а': 8.01, 'и': 7.35, 'н': 6.70, 'т': 6.26,
        'с': 5.47, 'р': 4.73, 'в': 4.54, 'л': 4.40, 'к': 3.49, 'м': 3.21,
        'д': 2.98, 'п': 2.81, 'у': 2.62, 'я': 2.01, 'ы': 1.90, 'ь': 1.74,
        'г': 1.70, 'з': 1.65, 'б': 1.59, 'ч': 1.44, 'й': 1.21, 'х': 0.97,
        'ж': 0.94, 'ш': 0.73, 'ю': 0.64, 'ц': 0.48, 'щ': 0.36, 'э': 0.32,
        'ф': 0.26, 'ъ': 0.04, 'ё': 0.04
    }
    
    # Оптимальные стартовые слова (покрывают частые буквы)
    STARTER_WORDS = ['адрес', 'стена', 'рейка', 'тоска', 'ление', 'окрас']

    def __init__(self, dictionary_path='dictionary.txt'):
        """Инициализация объекта с прочтением слов длиной в 5 букв из файла"""
        try:
            with open(dictionary_path, 'r', encoding='utf-8') as file:
                self.words = [word.strip().lower() for word in file if len(word.strip()) == 5]
        except FileNotFoundError:
            raise WordleHelperError(f"Файл словаря '{dictionary_path}' не найден")
        except UnicodeDecodeError:
            raise WordleHelperError(f"Ошибка кодировки файла '{dictionary_path}'")
        except Exception as e:
            raise WordleHelperError(f"Ошибка чтения файла '{dictionary_path}': {e}")
        
        if not self.words:
            raise WordleHelperError("Словарь пуст или не содержит слов длиной 5 букв")
        
        # Создаем индекс для быстрого поиска
        self.original_words_count = len(self.words)
    
    def find_words(self, known='_____', unknown='', excluded='', sort_by_frequency=True, limit=None):
        """Найти слова по заданным критериям"""
        # Валидация входных данных
        self._validate_inputs(known, unknown, excluded)
        
        # Приведение всех входных параметров к нижнему регистру
        known = known.lower()
        unknown = unknown.lower()
        excluded = excluded.lower()

        # Проверка конфликтов между known, unknown и excluded
        self._check_conflicts(known, unknown, excluded)

        # Статистика фильтрации
        stats = {'original': len(self.words)}

        # Генерация шаблона по известным позициям букв
        pattern = self._generate_pattern(known)
        # Фильтрация слов по шаблону
        filtered_words = self._filter_words_by_pattern(pattern)
        stats['after_pattern'] = len(filtered_words)

        # Фильтрация слов по включенным буквам
        if unknown:
            filtered_words = self._filter_words_by_inclusion(filtered_words, unknown)
            stats['after_inclusion'] = len(filtered_words)

        # Фильтрация слов по исключенным буквам
        if excluded:
            filtered_words = self._filter_words_by_exclusion(filtered_words, excluded)
            stats['after_exclusion'] = len(filtered_words)

        # Сортировка по частотности
        if sort_by_frequency and filtered_words:
            filtered_words = self._sort_by_frequency(filtered_words)

        # Ограничение количества результатов
        if limit and len(filtered_words) > limit:
            filtered_words = filtered_words[:limit]

        return filtered_words, stats

    def _validate_inputs(self, known, unknown, excluded):
        """Валидация входных параметров"""
        # Проверка known
        if len(known) != 5:
            raise ValidationError(f"Параметр known должен содержать ровно 5 символов, получено: {len(known)}")
        
        if not re.match(r'^[а-яё_]+$', known.lower()):
            raise ValidationError("Параметр known должен содержать только русские буквы и символ '_'")
        
        # Проверка unknown
        if unknown and not re.match(r'^[а-яё]+$', unknown.lower()):
            raise ValidationError("Параметр unknown должен содержать только русские буквы")
        
        # Проверка excluded
        if excluded and not re.match(r'^[а-яё]+$', excluded.lower()):
            raise ValidationError("Параметр excluded должен содержать только русские буквы")

    def _check_conflicts(self, known, unknown, excluded):
        """Проверка конфликтов между known, unknown и excluded буквами"""
        known_letters = set(known.replace('_', ''))
        unknown_letters = set(unknown) if unknown else set()
        excluded_letters = set(excluded) if excluded else set()
        
        # Конфликт 1: known vs unknown
        conflicts_unknown = known_letters & unknown_letters
        if conflicts_unknown:
            raise ValidationError(
                f"Буквы {', '.join(sorted(conflicts_unknown))} указаны и в known, и в unknown. "
                "Это противоречие - если позиция буквы известна, она не может быть 'неизвестной'"
            )
        
        # Конфликт 2: known vs excluded  
        conflicts_excluded = known_letters & excluded_letters
        if conflicts_excluded:
            raise ValidationError(
                f"Буквы {', '.join(sorted(conflicts_excluded))} указаны и в known, и в excluded. "
                "Это противоречие - если буква точно есть в слове, она не может быть исключена"
            )
            
        # Конфликт 3: unknown vs excluded
        conflicts_both = unknown_letters & excluded_letters  
        if conflicts_both:
            raise ValidationError(
                f"Буквы {', '.join(sorted(conflicts_both))} указаны и в unknown, и в excluded. "
                "Это противоречие - буква не может одновременно присутствовать и отсутствовать"
            )

    def _generate_pattern(self, known):
        """Замена нижних подчеркиваний на точки для создания регулярного выражения"""
        return known.replace('_', '.')

    def _filter_words_by_pattern(self, pattern):
        """Создание и применение регулярного выражения на список слов"""
        try:
            regex = re.compile(f'^{pattern}$')
            return [word for word in self.words if regex.match(word)]
        except re.error as e:
            raise ValidationError(f"Ошибка в шаблоне: {e}")

    def _filter_words_by_inclusion(self, words, unknown):
        """Фильтрация слов, содержащих все заданные буквы с учетом количества"""
        unknown_counter = Counter(unknown)
        
        filtered_words = []
        for word in words:
            word_counter = Counter(word)
            # Проверяем что в слове есть ВСЕ буквы из unknown в нужном количестве
            if all(word_counter[letter] >= count for letter, count in unknown_counter.items()):
                filtered_words.append(word)
        
        return filtered_words

    def _filter_words_by_exclusion(self, words, excluded):
        """Фильтрация слов, не содержащих ни одной из указанных букв"""
        excluded_set = set(excluded)
        return [word for word in words if not any(letter in excluded_set for letter in word)]

    def _sort_by_frequency(self, words):
        """Сортировка слов по частотности букв"""
        def word_frequency_score(word):
            return sum(self.LETTER_FREQUENCIES.get(letter, 0) for letter in word)
        
        return sorted(words, key=word_frequency_score, reverse=True)

    def get_letter_stats(self, words):
        """Получить статистику по буквам в словах"""
        if not words:
            return {}
        
        letter_counts = Counter()
        position_counts = defaultdict(Counter)
        
        for word in words:
            for i, letter in enumerate(word):
                letter_counts[letter] += 1
                position_counts[i][letter] += 1
        
        total_words = len(words)
        return {
            'letter_frequency': {letter: count/total_words*100 for letter, count in letter_counts.most_common()},
            'position_frequency': {pos: {letter: count/total_words*100 for letter, count in pos_counts.most_common()} 
                                 for pos, pos_counts in position_counts.items()}
        }

    def suggest_next_word(self, current_words, excluded_letters=set(), known='_____', unknown=''):
        """Предложить оптимальное следующее слово для максимального исключения вариантов"""
        if not current_words:
            # Если слов не осталось, предлагаем стартовое слово
            available_starters = [word for word in self.STARTER_WORDS 
                                if word in self.words and not any(letter in excluded_letters for letter in word)]
            return available_starters[0] if available_starters else random.choice(self.words)
        
        if len(current_words) <= 2:
            # Если слов очень мало, просто берем первое из найденных
            return current_words[0]
        
        if len(current_words) <= 5:
            # Если слов мало, предлагаем один из найденных вариантов
            return current_words[len(current_words)//2]  # Берем средний по рейтингу
        
        # Для большого количества вариантов ищем оптимальное слово для разделения
        best_word = None
        best_score = -1
        
        # Сначала пробуем слова из найденных вариантов
        candidate_words = current_words[:10]  # Топ-10 найденных слов
        
        # Добавляем некоторые слова из словаря, которые не противоречат ограничениям
        additional_candidates = []
        for word in self.words:
            if not any(letter in excluded_letters for letter in word):
                # Проверяем что слово не противоречит known позициям
                valid = True
                for i, letter in enumerate(known):
                    if letter != '_' and (i >= len(word) or word[i] != letter):
                        valid = False
                        break
                if valid:
                    additional_candidates.append(word)
                    if len(additional_candidates) >= 20:  # Ограничиваем для производительности
                        break
        
        candidate_words.extend(additional_candidates)
        
        for candidate in candidate_words:
            # Подсчитываем, сколько групп получится при использовании этого слова
            groups = defaultdict(int)
            for word in current_words:
                pattern = self._compare_words(candidate, word)
                groups[pattern] += 1
            
            # Лучший кандидат - тот, который создает наиболее равномерное разбиение
            # И приоритет отдаем словам из найденных вариантов
            diversity_score = len(groups) - max(groups.values()) / len(current_words)
            is_from_results = 1 if candidate in current_words else 0
            score = diversity_score + is_from_results * 0.5
            
            if score > best_score:
                best_score = score
                best_word = candidate
        
        return best_word or current_words[0]

    def _compare_words(self, guess, target):
        """Сравнить слова и вернуть паттерн результата"""
        result = []
        for i, (g_letter, t_letter) in enumerate(zip(guess, target)):
            if g_letter == t_letter:
                result.append('+')  # правильная позиция
            elif g_letter in target:
                result.append('?')  # есть в слове, но не на этой позиции
            else:
                result.append('-')  # нет в слове
        return ''.join(result)

    def interactive_mode(self):
        """Интерактивный режим с пошаговыми подсказками"""
        print("🎯 WordleHelper - Интерактивный режим")
        print("=" * 50)
        print("Помогу вам решить головоломку пошагово!")
        print("Формат результата: +буква (правильно), ?буква (есть, но не здесь), -буква (нет в слове)")
        print("Пример: +м?о-т+р-а означает: м на месте, о есть но не здесь, т нет, р на месте, а нет")
        print()

        known = '_____'
        unknown = ''
        excluded = ''
        attempt = 1
        last_suggested_word = None
        
        while True:
            try:
                # Поиск текущих вариантов
                words, stats = self.find_words(known, unknown, excluded, limit=20)
                
                print(f"📊 Попытка {attempt}")
                print(f"Текущее состояние: known='{known}', unknown='{unknown}', excluded='{excluded}'")
                
                if not words:
                    print("❌ Подходящих слов не найдено. Возможно, есть ошибка в данных.")
                    break
                
                print(f"✅ Найдено {len(words)} слов (показаны первые 10):")
                for i, word in enumerate(words[:10], 1):
                    print(f"  {i:2}. {word}")
                
                if len(words) > 10:
                    print(f"     ... и ещё {len(words) - 10} слов")
                
                # Предложение следующего слова
                if len(words) > 1:
                    excluded_set = set(excluded)
                    suggested = self.suggest_next_word(words, excluded_set, known, unknown)
                    last_suggested_word = suggested
                    print(f"💡 Рекомендую попробовать: '{suggested.upper()}'")
                    print(f"   (это слово поможет максимально сузить поиск)")
                elif len(words) == 1:
                    print(f"🎉 Ответ найден: '{words[0].upper()}'!")
                    break
                
                print()
                
                # Ввод пользователя
                prompt = "Введите слово и результат (например: 'адрес ?а+д-р-е?с')"
                if last_suggested_word:
                    prompt += f" или только результат для '{last_suggested_word.upper()}'"
                prompt += " или 'quit' для выхода: "
                user_input = input(prompt).strip()
                
                if user_input.lower() in ['quit', 'выход', 'q']:
                    print("👋 До свидания!")
                    break
                
                if not user_input:
                    continue
                
                # Парсинг ввода - может быть как "слово +с-т-е-н?а" так и "слово +++--"
                parts = user_input.split(maxsplit=1)
                if len(parts) == 1 and last_suggested_word:
                    # Пользователь ввел только результат для предложенного слова
                    word = last_suggested_word
                    result_input = parts[0]
                    print(f"🎯 Применяю результат к предложенному слову: '{word.upper()}'")
                    print(f"   Если вы имели в виду другое слово, введите: слово результат")
                elif len(parts) == 2:
                    word, result_input = parts
                else:
                    print("❌ Неверный формат. Используйте: 'слово результат'")
                    print("   Пример: адрес ?а+д-р-е?с")
                    if last_suggested_word:
                        print(f"   Или только результат: ?а+д-р-е?с (для слова '{last_suggested_word.upper()}')")
                    continue
                word = word.lower()
                
                if len(word) != 5:
                    print(f"❌ Слово должно содержать ровно 5 букв, получено: {len(word)}")
                    continue
                
                # Парсинг результата - извлекаем только символы статуса
                result = ""
                i = 0
                while i < len(result_input) and len(result) < 5:
                    char = result_input[i]
                    if char in "+-?":
                        result += char
                    i += 1
                
                if len(result) != 5:
                    print(f"❌ Результат должен содержать ровно 5 символов статуса (+, -, ?), получено: {len(result)}")
                    print("   Используйте: + (правильно), ? (есть но не здесь), - (нет в слове)")
                    print(f"   Найдено статусов: '{result}'")
                    continue
                
                # Обновление критериев на основе результата
                new_known = list(known)
                new_unknown = list(unknown)
                new_excluded = list(excluded)
                
                # Сначала обрабатываем все '+' чтобы зафиксировать known буквы
                for i, (letter, status) in enumerate(zip(word, result)):
                    if status == '+':
                        new_known[i] = letter

                # Теперь обрабатываем '?' и '-' с учетом уже зафиксированных букв
                for i, (letter, status) in enumerate(zip(word, result)):
                    if status == '+':
                        # Убираем из unknown если была там (буква уже зафиксирована)
                        while letter in new_unknown:
                            new_unknown.remove(letter)
                    elif status == '?':
                        # Буква есть в слове, но не на этой позиции
                        if letter not in new_unknown and letter not in ''.join(new_known):
                            new_unknown.append(letter)
                    elif status == '-':
                        # Буква помечена как отсутствующая на этой позиции
                        # Проверяем есть ли она уже в known позициях
                        known_string = ''.join(new_known)
                        if letter not in known_string:
                            # Буквы вообще нет в слове
                            if letter not in new_excluded:
                                new_excluded.append(letter)
                            # Убираем из unknown если была там
                            while letter in new_unknown:
                                new_unknown.remove(letter)
                        # Если буква уже есть в known, то "-" означает что дополнительных 
                        # экземпляров этой буквы нет - пока не обрабатываем этот случай
                
                known = ''.join(new_known)
                unknown = ''.join(new_unknown)
                excluded = ''.join(new_excluded)
                
                attempt += 1
                print()
                
            except KeyboardInterrupt:
                print("\n👋 Прерывание пользователем")
                break
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                continue


def main():
    parser = argparse.ArgumentParser(description="Помощник для игры в '5 слов'.",
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog="""
Примеры использования:
  python3 main.py --known "м_тр_" --unknown "о" --excluded "узк"
  python3 main.py --interactive
  python3 main.py --known "_а___" --stats
  python3 main.py --suggest --excluded "абвг"
""")
    
    parser.add_argument('--known', type=str, default='_____', help='Буквы на известных позициях. Пример: м_тр_')
    parser.add_argument('--unknown', type=str, default='', help='Буквы, присутствующие в слове, но позиция неизвестна.')
    parser.add_argument('--excluded', type=str, default='', help='Буквы, отсутствующие в слове.')
    parser.add_argument('--limit', type=int, help='Максимальное количество результатов')
    parser.add_argument('--no-sort', action='store_true', help='Отключить сортировку по частотности')
    parser.add_argument('--stats', action='store_true', help='Показать статистику по буквам')
    parser.add_argument('--suggest', action='store_true', help='Предложить оптимальное следующее слово')
    parser.add_argument('--interactive', action='store_true', help='Интерактивный режим')

    args = parser.parse_args()

    try:
        helper = WordleHelper()
        
        # Интерактивный режим
        if args.interactive:
            helper.interactive_mode()
            return
        
        # Обычный режим
        sort_by_frequency = not args.no_sort
        results, stats = helper.find_words(
            args.known, args.unknown, args.excluded, 
            sort_by_frequency=sort_by_frequency, 
            limit=args.limit
        )
        
        # Вывод результатов
        if results:
            print(f"✅ Найдено {len(results)} подходящих слов:")
            
            # Предупреждение о большом количестве результатов
            if len(results) > 50 and not args.limit:
                print(f"⚠️  Результатов много! Показаны первые 20. Используйте --limit для изменения.")
                results = results[:20]
            
            for word in results:
                print(f"  {word}")
            
            # Статистика фильтрации
            print(f"\n📊 Статистика фильтрации:")
            print(f"  Исходно слов: {stats['original']}")
            if 'after_pattern' in stats:
                print(f"  После шаблона: {stats['after_pattern']}")
            if 'after_inclusion' in stats:
                print(f"  После включения: {stats['after_inclusion']}")
            if 'after_exclusion' in stats:
                print(f"  После исключения: {stats['after_exclusion']}")
        else:
            print("❌ Подходящих слов не найдено.")
        
        # Статистика по буквам
        if args.stats and results:
            stats_data = helper.get_letter_stats(results)
            print(f"\n📈 Статистика по буквам:")
            print("Самые частые буквы в найденных словах:")
            for letter, freq in list(stats_data['letter_frequency'].items())[:10]:
                print(f"  {letter}: {freq:.1f}%")
        
        # Предложение следующего слова
        if args.suggest:
            excluded_set = set(args.excluded.lower())
            suggested = helper.suggest_next_word(results, excluded_set, args.known.lower(), args.unknown.lower())
            print(f"\n💡 Рекомендуемое слово для проверки: '{suggested.upper()}'")
    
    except WordleHelperError as e:
        print(f"❌ Ошибка: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Прерывание пользователем", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()