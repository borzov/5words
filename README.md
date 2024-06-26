# WordleHelper

WordleHelper - это скрипт, который помогает отгадывать слова в игре "5 слов", используя заданные известные и неизвестные буквы, а также буквы, которые точно отсутствуют в слове.

## Описание

Этот скрипт позволяет фильтровать слова из словаря на основе следующих параметров:
-  Известные буквы на определенных позициях.
-  Неизвестные буквы, которые точно присутствуют в слове.
-  Буквы, которые точно отсутствуют в слове.

## Использование

Для запуска скрипта используйте следующую команду:

```sh
python3 main.py [options]
```

### Опции

-  `--known`: Буквы на известных позициях. Пример: `м_тр_`
-  `--unknown`: Буквы, присутствующие в слове, но позиция неизвестна. Пример: `оа`
-  `--excluded`: Буквы, отсутствующие в слове. Пример: `узк`

### Примеры

1. **Поиск слов с известными буквами на определенных позициях:**
   ```sh
   python3 main.py --known "м_тр_"
   ```
   Выводит слова, в которых первая буква "м", третья буква "т" и пятая буква "р".

2. **Поиск слов с известными буквами, но неизвестной позицией:**
   ```sh
   python3 main.py --unknown "оа"
   ```
   Выводит слова, которые содержат буквы "о" и "а" в любом месте.

3. **Поиск слов с исключенными буквами:**
   ```sh
   python3 main.py --excluded "узк"
   ```
   Выводит слова, которые не содержат буквы "у", "з" и "к".

4. **Комбинированный поиск:**
   ```sh
   python3 main.py --known "м_тр_" --unknown "оа" --excluded "узк"
   ```
   Комбинирует все фильтры: первое, третье и пятое место заняты буквами "м", "т" и "р" соответственно, слово содержит буквы "о" и "а", но не содержит буквы "у", "з" и "к".

## Автор

Maksim Borzov

## Лицензия

Этот проект лицензируется на условиях лицензии MIT - подробности см. в файле `LICENSE`.