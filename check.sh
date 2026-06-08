#!/bin/bash
# Скрипт для проверки задачи
# Использование: ./check.sh путь/к/задаче

TASK_PATH=$1

if [ -z "$TASK_PATH" ]; then
    echo "❌ Укажи путь к задаче!"
    echo "Пример: ./check.sh 01.2.BasicTypes/tasks/hello_world/"
    exit 1
fi

cd ~/python-course/iver88
source shad_env/bin/activate

echo "========================================="
echo "🔍 ЗАПУСК ТЕСТОВ"
echo "========================================="
pytest $TASK_PATH -v
TEST_RESULT=$?

echo "========================================="
echo "🔍 ПРОВЕРКА ТИПОВ"
echo "========================================="
pyrefly check $TASK_PATH
TYPECHECK_RESULT=$?

echo "========================================="
echo "🔍 ПРОВЕРКА СТИЛЯ"
echo "========================================="
ruff check $TASK_PATH
RUFF_RESULT=$?

echo "========================================="
if [ $TEST_RESULT -eq 0 ] && [ $TYPECHECK_RESULT -eq 0 ] && [ $RUFF_RESULT -eq 0 ]; then
    echo "✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ! Можно пушить."
else
    echo "❌ ЕСТЬ ОШИБКИ! Исправь перед пушем."
fi
