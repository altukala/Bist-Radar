#!/bin/zsh

# Bu dosyaya çift tıklamak BIST30 trend taramasını çalıştırır.
cd "$(dirname "$0")"
source .venv/bin/activate
python radar.py

echo ""
echo "Tarama tamamlandı. Bu pencereyi kapatmak için bir tuşa bas."
read -n 1
