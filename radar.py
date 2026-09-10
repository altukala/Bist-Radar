"""BIST30 için basit fiyat ve trend özeti."""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import certifi

# Bazı macOS/Python kurulumlarında piyasa verisi bağlantısı için gerekir.
os.environ.setdefault("SSL_CERT_FILE", certifi.where())

import borsapy as bp


def analyze_stock(symbol: str) -> dict[str, object]:
    """Bir hissenin fiyat trendini ve bu trendin nedenlerini hesaplar."""
    prices = bp.Ticker(symbol).history(period="3mo")
    closes = prices["Close"].dropna()
    if len(closes) < 21:
        raise ValueError("Yeterli fiyat geçmişi alınamadı.")

    last_price = float(closes.iloc[-1])
    return_5d = (last_price / float(closes.iloc[-6]) - 1) * 100
    return_20d = (last_price / float(closes.iloc[-21]) - 1) * 100
    sma_20 = float(closes.tail(20).mean())
    sma_50 = float(closes.tail(50).mean())
    distance_sma20 = (last_price / sma_20 - 1) * 100
    distance_sma50 = (last_price / sma_50 - 1) * 100
    annualized_volatility = float(closes.pct_change().dropna().tail(20).std() * (252**0.5) * 100)

    if return_5d > 0 and return_20d > 0 and distance_sma20 > 0:
        trend = "Güçlü pozitif"
    elif return_20d > 0 and distance_sma20 > 0:
        trend = "Pozitif"
    elif return_5d < 0 and return_20d < 0 and distance_sma20 < 0:
        trend = "Negatif"
    else:
        trend = "Karışık"

    reasons = [
        f"20 günde {return_20d:+.1f}%",
        f"fiyat 20 günlük ortalamaya göre {distance_sma20:+.1f}%",
        f"50 günlük ortalamaya göre {distance_sma50:+.1f}%",
    ]
    if annualized_volatility >= 60:
        reasons.append(f"yüksek oynaklık ({annualized_volatility:.0f}%)")
    else:
        reasons.append(f"orta/düşük oynaklık ({annualized_volatility:.0f}%)")

    return {
        "symbol": symbol,
        "last_price": last_price,
        "return_5d": return_5d,
        "return_20d": return_20d,
        "distance_sma20": distance_sma20,
        "distance_sma50": distance_sma50,
        "annualized_volatility": annualized_volatility,
        "trend": trend,
        "reasons": reasons,
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
    print("-" * 60)
    for item in results:
        print(
            f"{item['symbol']:<8} {item['last_price']:>12.2f} "
            f"{item['return_5d']:>+8.2f}% {item['return_20d']:>+8.2f}%  {item['trend']}"
        )

    print("\nNeden bu trend? (her satır fiyat verisine dayanır)")
    print("-" * 60)
    for item in results:
        print(f"{item['symbol']}: {item['trend']} — " + "; ".join(item["reasons"]))

    print(f"\nBaşarıyla taranan hisse: {len(results)}/{len(symbols)}")
    if failures:
        print("Alınamayan veriler:")
        print("\n".join(f"- {failure}" for failure in failures))


if __name__ == "__main__":
    main()
