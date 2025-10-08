#!/bin/bash

APP_DIR="/home/mark/sites/cardspb4"
MAIN_LOG="$APP_DIR/main.log"
BOT_LOG="$APP_DIR/bot.log"

start() {
  echo "🚀 Запуск main (FastAPI)..."
  cd "$APP_DIR"
  nohup uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 --proxy-headers > "$MAIN_LOG" 2>&1 &
  echo $! > "$APP_DIR/main.pid"
  echo "main запущен (PID=$(cat $APP_DIR/main.pid)), лог: $MAIN_LOG"

  echo "🤖 Запуск bot..."
  nohup python3 -m bot.bot > "$BOT_LOG" 2>&1 &
  echo $! > "$APP_DIR/bot.pid"
  echo "bot запущен (PID=$(cat $APP_DIR/bot.pid)), лог: $BOT_LOG"
}

stop() {
  echo "⏹ Остановка процессов..."
  if [ -f "$APP_DIR/main.pid" ]; then
    kill -9 $(cat "$APP_DIR/main.pid") 2>/dev/null || true
    rm -f "$APP_DIR/main.pid"
    echo "main остановлен"
  fi
  if [ -f "$APP_DIR/bot.pid" ]; then
    kill -9 $(cat "$APP_DIR/bot.pid") 2>/dev/null || true
    rm -f "$APP_DIR/bot.pid"
    echo "bot остановлен"
  fi
}

status() {
  echo "📊 Статус:"
  if [ -f "$APP_DIR/main.pid" ] && ps -p $(cat "$APP_DIR/main.pid") > /dev/null; then
    echo "main работает (PID=$(cat $APP_DIR/main.pid))"
  else
    echo "main не запущен"
  fi

  if [ -f "$APP_DIR/bot.pid" ] && ps -p $(cat "$APP_DIR/bot.pid") > /dev/null; then
    echo "bot работает (PID=$(cat $APP_DIR/bot.pid))"
  else
    echo "bot не запущен"
  fi
}

case "$1" in
  start)
    start
    ;;
  stop)
    stop
    ;;
  restart)
    stop
    sleep 1
    start
    ;;
  status)
    status
    ;;
  *)
    echo "Использование: $0 {start|stop|restart|status}"
    exit 1
    ;;
esac
