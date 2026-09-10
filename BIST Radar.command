#!/bin/zsh

# BIST Radar'ın tek giriş noktası.
cd "$(dirname "$0")"
source .venv/bin/activate

while true; do
  clear
  echo "========================================"
  echo "              BIST RADAR"
  echo "========================================"
  echo ""
  echo "1) BIST30 genel görünüm"
  echo "   Tüm BIST30 hisselerinin kısa/orta vadeli trendini gösterir."
  echo ""
  echo "2) Tek hisse analizi"
  echo "   Trend, finansal kalite ve dikkat noktalarını birleştirir."
  echo ""
  echo "3) Hisse karşılaştır"
  echo "   2-5 hisseyi trend ve temel finansal ölçütlerde karşılaştırır."
  echo ""
  echo "4) Şirket kalitesi"
  echo "   Bir hissenin kârlılık, borç ve nakit üretimini gösterir."
  echo ""
  echo "5) Görsel rapor oluştur"
  echo "   Seçtiğin hisse için tarayıcıda sade bir özet açar."
  echo ""
  echo "6) BIST30 görsel genel görünüm"
  echo "   Tüm BIST30 hisselerini tarayıcıda filtrelenebilir tabloda gösterir."
  echo ""
  echo "7) Fırsat taraması"
  echo "   Şeffaf kurallarla araştırma önceliği oluşturan BIST30 filtresi."
  echo ""
  echo "8) TEFAS fon tarama"
  echo "   Yatırım fonlarının getiri görünümünü ayrı bir ekranda gösterir."
  echo ""
  echo "9) ABD piyasaları fırsat tarama"
  echo "   Büyük ve likit ABD şirketlerini açık kurallarla araştırma için listeler."
  echo ""
  echo "0) Çıkış"
  echo ""
  echo -n "Seçimin (0-9): "
  read CHOICE

  case "$CHOICE" in
    1) python radar.py ;;
    2)
      echo -n "Hisse kodu (örnek: THYAO): "
      read SYMBOL
      python analiz.py "$SYMBOL"
      ;;
    3)
      echo "2-5 hisse kodunu boşlukla yaz (örnek: THYAO TUPRS ASELS):"
      read -A SYMBOLS
      python karsilastir.py "${SYMBOLS[@]}"
      ;;
    4)
      echo -n "Hisse kodu (örnek: THYAO): "
      read SYMBOL
      python kalite.py "$SYMBOL"
      ;;
    5)
      echo -n "Hisse kodu (örnek: THYAO): "
      read SYMBOL
      python rapor.py "$SYMBOL"
      ;;
    6) python bist30_rapor.py ;;
    7) python firsat_raporu.py ;;
    8) python fon_tara.py ;;
    9) python abd_firsat_tara.py ;;
    0) exit 0 ;;
    *)
      echo "Geçerli bir seçim yapmadın."
      ;;
  esac

  echo ""
  echo "Ana menüye dönmek için bir tuşa bas."
  read
done
