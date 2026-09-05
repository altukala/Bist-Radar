"""BIST30 için basit fiyat ve trend özeti."""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import certifi

# Bazı macOS/Python kurulumlarında piyasa verisi bağlantısı için gerekir.
os.environ.setdefault("SSL_CERT_FILE", certifi.where())

import borsapy as bp


def analyze_stock(symbol: str) -> dict[str, object]:
    """Bir hissenin son fiyatını ve 5/20 işlem günlük performansını hesaplar."""
    prices = bp.Ticker(symbol).history(period="3mo")
    closes = prices["Close"].dropna()
    if len(closes) < 21:
        raise ValueError("Yeterli fiyat geçmişi alınamadı.")

    last_price = float(closes.iloc[-1])
    return_5d = (last_price / float(closes.iloc[-6]) - 1) * 100
    return_20d = (last_price / float(closes.iloc[-21]) - 1) * 100

    if return_5d > 0 and return_20d > 0:
        trend = "Güçlü pozitif"
    elif return_20d > 0:
        trend = "Pozitif"
    elif return_5d < 0 and return_20d < 0:
        trend = "Negatif"
    else:
        trend = "Karışık"

    return {
        "symbol": symbol,
        "last_price": last_price,
        "return_5d": return_5d,
        "return_20d": return_20d,
        "trend": trend,
    }


def main() -> None:
    symbols = bp.Index("XU030").component_symbols
    results: list[dict[str, object]] = []
    failures: list[str] = []

    print("BIST30 trend taraması hazırlanıyor...\n")
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(analyze_stock, symbol): symbol for symbol in symbols}
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                results.append(future.result())
            except Exception as error:
                failures.append(f"{symbol}: {error}")

    results.sort(key=lambda item: float(item["return_20d"]), reverse=True)
    print(f"{'Hisse':<8} {'Son Fiyat':>12} {'5 Gün':>9} {'20 Gün':>9}  Trend")
    print("-" * 58)
    for item in results:
        print(
            f"{item['symbol']:<8} {item['last_price']:>12.2f} "
            f"{item['return_5d']:>+8.2f}% {item['return_20d']:>+8.2f}%  {item['trend']}"
        )

    print(f"\nBaşarıyla taranan hisse: {len(results)}/{len(symbols)}")
    if failures:
        print("Alınamayan veriler:")
        print("\n".join(f"- {failure}" for failure in failures))


if __name__ == "__main__":
    main()
