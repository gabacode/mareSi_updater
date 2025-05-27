# mareSi updater

### Run with Docker

```
docker run --rm \
 -v "$PWD":/app \
 -e OPENSSL_CONF=config/openssl.cnf \
 -w /app \
 area-updater python3 update.py
```

```
docker run --rm \
 -v "$PWD":/app \
 -w /app \
 area-updater python3 diff.py
```
