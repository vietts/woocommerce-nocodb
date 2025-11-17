#!/bin/bash
# check_scheduler.sh - Check if scheduler is running

echo "🔍 Checking scheduler instances..."
echo ""

# Count running instances
COUNT=$(ps aux | grep "python3 scheduler.py" | grep -v grep | wc -l)

if [ $COUNT -eq 0 ]; then
    echo "❌ Scheduler NOT running"
    echo ""
    echo "To start it:"
    echo "  cd ~/telegram-notion-scheduler"
    echo "  source venv/bin/activate"
    echo "  python3 scheduler.py"
    exit 1
elif [ $COUNT -eq 1 ]; then
    echo "✅ ONE scheduler running (correct!)"
    echo ""
    ps aux | grep "python3 scheduler.py" | grep -v grep
    exit 0
else
    echo "⚠️  DUPLICATES DETECTED! Found $COUNT instances"
    echo ""
    ps aux | grep "python3 scheduler.py" | grep -v grep
    echo ""
    echo "To fix, run:"
    echo "  pkill -9 -f 'python3 scheduler.py'"
    echo "  cd ~/telegram-notion-scheduler && source venv/bin/activate && python3 scheduler.py"
    exit 1
fi
