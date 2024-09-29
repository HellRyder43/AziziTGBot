# This script works for both PowerShell and Bash

# Create a virtual environment
if ($PSVersionTable.PSVersion.Major -ge 3) {
    python -m venv telegram_bot_env
} else {
    py -m venv telegram_bot_env
}

# Activate the virtual environment
if ($PSVersionTable.PSEdition -eq "Core") {
    # PowerShell Core
    & telegram_bot_env/bin/Activate.ps1
} elseif ($PSVersionTable.PSEdition -eq "Desktop") {
    # Windows PowerShell
    & telegram_bot_env\Scripts\Activate.ps1
} else {
    # Bash
    source telegram_bot_env/bin/activate
}

# Install required packages
pip install python-telegram-bot google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

# Create a new Python file for the bot
if ($PSVersionTable.PSVersion.Major -ge 3) {
    New-Item -ItemType File -Path . -Name property_bot.py
} else {
    echo $null > property_bot.py
}

Write-Output "Development environment set up complete. You can now start coding in property_bot.py"