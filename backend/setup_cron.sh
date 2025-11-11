# TODO

#!/bin/bash
# Setup script for daily database refresh via cron

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration
BACKEND_DIR="$SCRIPT_DIR"
LOG_DIR="$BACKEND_DIR/logs"
PYTHON_PATH="$BACKEND_DIR/venv/bin/python"
REFRESH_SCRIPT="$BACKEND_DIR/refresh_database.py"

# Create logs directory
mkdir -p "$LOG_DIR"

# Make the refresh script executable
chmod +x "$REFRESH_SCRIPT"

echo "Setting up daily refresh for Vinted Fashion Recommender"
echo "Backend directory: $BACKEND_DIR"
echo "Log directory: $LOG_DIR"

# Check if virtual environment exists
if [ ! -f "$PYTHON_PATH" ]; then
    echo "Error: Virtual environment not found at $PYTHON_PATH"
    echo "Please create a virtual environment first:"
    echo "  cd $BACKEND_DIR"
    echo "  python -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Create cron job entry
CRON_ENTRY="0 2 * * * cd $BACKEND_DIR && $PYTHON_PATH $REFRESH_SCRIPT --catalog-ids 10 --max-pages 10 --log-file $LOG_DIR/refresh.log >> $LOG_DIR/cron.log 2>&1"

echo ""
echo "Cron job entry to add:"
echo "$CRON_ENTRY"
echo ""

# Ask user if they want to add the cron job
read -p "Do you want to add this cron job automatically? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    echo "Cron job added successfully!"
    echo "The database will be refreshed daily at 2:00 AM"
else
    echo "Cron job not added. You can add it manually later using:"
    echo "crontab -e"
    echo "Then add this line:"
    echo "$CRON_ENTRY"
fi

echo ""
echo "Setup complete!"
echo ""
echo "To test the refresh manually, run:"
echo "  cd $BACKEND_DIR"
echo "  $PYTHON_PATH $REFRESH_SCRIPT --dry-run"
echo ""
echo "To run the actual refresh:"
echo "  cd $BACKEND_DIR"
echo "  $PYTHON_PATH $REFRESH_SCRIPT"
echo ""
echo "Logs will be written to: $LOG_DIR"
