# DevOpsTask

## Инструкция

### Установка зависимостей

```
pip install paramiko psycopg2-binary
```

### Запуск

```
python install_postgresql.py server1,server2
```

### Принятые решения и вопросы

1. Выбор наименее нагруженного сервера: Используется средняя загрузка за 15 минут из вывода uptime
2. Реализована проверка через выполнение запроса SELECT 1
3. В коде стоит заглушка на путь  - его нужно заменить на реальный путь к приватному ключу.
4. Определение типа ОС реализовано через анализ /etc/os-release