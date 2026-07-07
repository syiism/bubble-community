#!/bin/sh
set -e

export DB_HOST="127.0.0.1"
export DB_PORT="3306"
export DB_USER="root"
export DB_PASSWORD=""
export DB_NAME="bubble_community"

echo "[entrypoint] Initializing MySQL..."
mkdir -p /var/lib/mysql /var/run/mysqld
chown -R mysql:mysql /var/lib/mysql /var/run/mysqld

if [ ! -d /var/lib/mysql/mysql ]; then
    echo "[entrypoint] Creating initial MySQL database..."
    mysqld --initialize-insecure --user=mysql
fi

echo "[entrypoint] Starting MySQL..."
mysqld --user=mysql --bind-address=127.0.0.1 &
MYSQL_PID=$!

echo "[entrypoint] Waiting for MySQL to be ready..."
for i in $(seq 1 60); do
    if mysqladmin ping -u root --silent; then
        echo "[entrypoint] MySQL is ready."
        break
    fi
    if [ $i -eq 60 ]; then
        echo "[entrypoint] MySQL failed to start"
        exit 1
    fi
    sleep 1
done

echo "[entrypoint] Configuring MySQL users..."
mysql -u root <<EOF
ALTER USER 'root'@'localhost' IDENTIFIED BY '';
CREATE USER IF NOT EXISTS 'root'@'127.0.0.1' IDENTIFIED BY '';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost' WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON *.* TO 'root'@'127.0.0.1' WITH GRANT OPTION;
FLUSH PRIVILEGES;
EOF

cd /app/backend

echo "[entrypoint] Running seed..."
uv run python -m app.seed

echo "[entrypoint] Starting uvicorn..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 7860