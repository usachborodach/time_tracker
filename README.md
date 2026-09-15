# Time Tracker

## Установка

```bash
apt install python3.10-venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
deactivate
```

## Конфигурация `.env`

```
cp .env.example .env
```

```bash
# SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"

# PASSWORD_HASH
python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('мой_пароль'))"
```

## Локальный запуск

```bash
flask --app wsgi create-index
python run.py
```

## Продакшен (systemd + nginx + gunicorn)

```bash
mkdir -p /var/log/time_tracker

ln -sf \
  /root/time_tracker/deploy/time_tracker.service \
  /etc/systemd/system/time_tracker.service
systemctl daemon-reload
systemctl enable --now time_tracker

ln -sf \
  /root/time_tracker/deploy/nginx.conf \
  /etc/nginx/sites-enabled/time_tracker
nginx -t && systemctl restart nginx

# logrotate
ln -sf /root/time_tracker/deploy/time_tracker.logrotate \
       /etc/logrotate.d/time_tracker
```

## Запуск тестов

```bash
pytest -q
```