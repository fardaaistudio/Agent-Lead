#!/usr/bin/env bash
# Installs common Linux dependencies required by Playwright browsers.
set -e
echo "This script requires sudo. Installing common Playwright deps..."
sudo apt-get update
sudo apt-get install -y \
  libx11-xcb1 \
  libxrandr2 \
  libxcomposite1 \
  libxcursor1 \
  libxdamage1 \
  libxfixes3 \
  libxi6 \
  libgtk-3-0 \
  libatk1.0-0 \
  libcairo2 \
  libcairo-gobject2 \
  libgdk-pixbuf2.0-0 \
  libasound2t64 \
  libpangocairo-1.0-0

echo "Done. You can now run: python -m playwright install"
