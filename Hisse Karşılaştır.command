#!/bin/zsh

cd "$(dirname "$0")"
source .venv/bin/activate

echo "2 ile 5 hisse kodunu boşlukla yaz (örnek: THYAO TUPRS ASELS):"
read -A SYMBOLS
python karsilastir.py "${SYMBOLS[@]}"

echo ""
echo "İşlem tamamlandı. Bu pencereyi kapatmak için bir tuşa bas."
read -n 1
