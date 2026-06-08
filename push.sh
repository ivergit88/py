#!/bin/bash
# Скрипт для отправки задачи
# Использование: ./push.sh путь/к/задаче "название задачи"

TASK_PATH=$1
TASK_NAME=$2

if [ -z "$TASK_PATH" ] || [ -z "$TASK_NAME" ]; then
    echo "❌ Укажи путь к задаче и название!"
    echo "Пример: ./push.sh 01.2.BasicTypes/tasks/hello_world/ hello_world"
    exit 1
fi

cd ~/python-course/iver88
source shad_env/bin/activate

echo "📦 Добавляю файлы..."
git add $TASK_PATH

echo "📝 Создаю коммит..."
git commit -m "Решение задачи $TASK_NAME"

echo "🚀 Отправляю в GitLab..."
git push origin main

echo "✅ Готово! Проверь пайплайн на gitlab.manytask.org"
