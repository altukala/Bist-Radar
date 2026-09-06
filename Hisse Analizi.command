#!/bin/zsh

cd "$(dirname "$0")"
source .venv/bin/activate

echo -n "Hisse kodunu yaz (örnek: THYAO): "
read SYMBOL
python analiz.py "$SYMBOL"

echo ""
echo "İşlem tamamlandı. Bu pencereyi kapatmak için bir tuşa bas."
read -n 1
