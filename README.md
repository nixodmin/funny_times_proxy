# funny_times_proxy

Это реализация простейшего Shadowsocks-like прокси сервера и клиента с AES-шифрованием на Python

Принцип работы:
1. У вас есть cервер(подразумевается Linux VPS) в другой стране, на нём настраиваем и запускаем скрипт ftproxy-server
2. У вас есть клиентская машина (ОС значения не имеет), на клиентской машине:

   2.1 Настраиваем и запускаем скрипт ftproxy-client

   2.2 В браузере указываем работающий скрипт ftproxy-client как SOCKS5 прокси

Итог: Зашифрованный трафик браузера идёт в обход всех DPI фильтров, Youtube снова не тормозит!

Важные моменты!

1. Работа скрипта требует установки библиотеки Crypto:
```
   pip install pycryptodome
```
3. Настройки ftproxy-server (ваш удалённый Shadowsocks-like сервер):
```
PASSWORD = "mysecretpassword"    # замените на ваш пароль (должен быть одинаковым в обоих файлах)
server.bind(("0.0.0.0", 8388))   # можно указать на каком именно интерфейсе (если их несколько) работать и можно заменить порт на другой (должен быть одинаковым в обоих файлах)
```
3. Настройки ftproxy-client (ваш локальный клиент и локальный SOCKS5 сервер):
```
PASSWORD = "mysecretpassword"    # замените на ваш пароль (должен быть одинаковым в обоих файлах)
SERVER_IP = "your-server-ip"     # укажите ip вашего удалённого сервера
SERVER_PORT = 8388               # укажите порт вашего удалённого сервера
proxy.bind(("127.0.0.1", 1080))  # клиентская часть это ещё и локальный сервер (SOCKS5 для вашего браузера) и по умолчанию работает на порту 1080, можно заменить на другой, если 1080 занят
```

# Тонкий тюнинг.

Для оптимизации при высоких нагрузках в обоих скриптах замените:
```
BUFFER_SIZE = 32768  # Увеличьте буфер для быстрых соединений
```

Можно ещё увеличить таймаут для медленных соединений, по умолчанию он 30 в обоих скриптах, поставить 45, например.

Автозапуск сервера (для Linux):

Создайте systemd-сервис (/etc/systemd/system/ftproxy_server.service):

```
[Unit]
Description=Funny Times Python Proxy Server
After=network.target

[Service]
User=root
WorkingDirectory=/path/to/your/script  # путь к скрипту
ExecStart=/usr/bin/python3 /path/to/your/script/ftproxy-server
Restart=always

[Install]
WantedBy=multi-user.target
```
Активация:
```
sudo systemctl enable ftproxy_server
sudo systemctl start ftproxy_server
```
# Логи
Если нужен мониторинг, добавьте в ftproxy-server:
```
import logging
logging.basicConfig(
    filename='ftproxy.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
```
Смотрим логи:
```
tail -f ftproxy.log            # Для сервера
journalctl -u ftproxy_server -f  # Для systemd, если нужно
```
