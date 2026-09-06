"""Birden çok BIST hissesini ayrı trend ve kalite ölçütleriyle karşılaştırır."""

import os
import sys
import time

import certifi

os.environ.setdefault("SSL_CERT_FILE", certifi.where())

from analiz import get_quality
from radar import analyze_stock


def row(symbol: str) -> dict[str, object]:
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            trend = analyze_stock(symbol)
            quality = get_quality(symbol)
            return {"symbol": symbol, **trend, **quality}
        except Exception as error:
            last_error = error
            if attempt == 0:
                print("  Veri bağlantısı yeniden deneniyor...")
                time.sleep(2)
    raise RuntimeError(str(last_error))


def print_ranking(title: str, results: list[dict[str, object]], key: str) -> None:
    print(f"\n{title}")
    for place, item in enumerate(sorted(results, key=lambda item: float(item[key]), reverse=True), start=1):
        print(f"{place}. {item['symbol']}: {float(item[key]):+.1f}%")


def main() -> None:
    raw_symbols = sys.argv[1:] or ["THYAO", "TUPRS", "ASELS"]
    symbols = [symbol.upper().strip() for symbol in raw_symbols if symbol.strip()]
    if not 2 <= len(symbols) <= 5:
        raise SystemExit("Lütfen 2 ile 5 arasında hisse kodu gir.")

    results = []
    failures = []
    print("\nHİSSE KARŞILAŞTIRMASI")
    print("Bu ekran bilgi amaçlıdır; tek bir toplam puan ya da al/sat önerisi üretmez.\n")
    for symbol in symbols:
        print(f"{symbol} analiz ediliyor...")
        try:
            results.append(row(symbol))
        except Exception as error:
            failures.append(f"{symbol}: {error}")

    if not results:
        print("\nHiçbir hissenin verisi alınamadı.")
        print("İnternet bağlantını kontrol edip birkaç dakika sonra tekrar dene.")
        return

    print(f"\n{'Hisse':<8} {'20 Gün':>9} {'Net Marj':>10} {'ROE':>9} {'Net Borç/Özk.':>15}")
    print("-" * 58)
    for item in results:
        print(
            f"{item['symbol']:<8} {item['return_20d']:>+8.1f}% "
            f"{item['net_margin']:>9.1f}% {item['roe']:>8.1f}% "
            f"{item['net_debt_to_equity']:>+14.1f}%"
        )

    print_ranking("20 günlük fiyat momentumu", results, "return_20d")
    print_ranking("Net kâr marjı", results, "net_margin")
    print_ranking("Özkaynak kârlılığı", results, "roe")

    print("\nNot: Net borç/özkaynakta daha düşük değer genellikle daha az borç baskısı anlamına gelir;")
    print("sektör farkları ve finansal şirketlerin farklı bilanço yapısı ayrıca dikkate alınmalıdır.")
    if failures:
        print("\nAlınamayan veriler:")
        for failure in failures:
            print(f"- {failure}")


if __name__ == "__main__":
    main()
