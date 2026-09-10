"""ABD büyük ölçekli hisseleri için şeffaf araştırma önceliği taraması."""

import html
import os
import webbrowser
from datetime import datetime
from pathlib import Path

import yfinance as yf

# İlk sürümün açık evreni: farklı sektörlerden büyük ve likit ABD şirketleri.
US_LARGE_CAP = [
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "AVGO", "TSLA", "BRK-B", "JPM",
    "V", "WMT", "LLY", "MA", "NFLX", "XOM", "COST", "ORCL", "JNJ", "PG",
    "HD", "ABBV", "BAC", "KO", "CVX", "CRM", "AMD", "MCD", "TMO", "CSCO",
    "ACN", "LIN", "GE", "NOW", "QCOM", "CAT", "AMGN", "DIS", "NKE", "GS",
]


def number(value) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def percent(value: float | None) -> str:
    return "—" if value is None else f"{value:+.1f}%"


def get_quality(symbol: str) -> dict[str, float | str | None]:
    info = yf.Ticker(symbol).get_info()
    return {
        "name": info.get("shortName") or symbol,
        "margin": number(info.get("profitMargins")),
        "roe": number(info.get("returnOnEquity")),
        "debt_to_equity": number(info.get("debtToEquity")),
        "operating_cashflow": number(info.get("operatingCashflow")),
        "pe": number(info.get("trailingPE")),
    }


def classify(item: dict) -> tuple[str, list[str]]:
    trend_ok = item["return_20d"] > 0 and item["distance_sma20"] > 0
    if not trend_ok:
        return "Dikkat", [
            f"20 günlük fiyat değişimi {item['return_20d']:+.1f}%.",
            "Fiyat 20 günlük ortalamaya göre güçlü değil.",
        ]

    quality = item.get("quality")
    if not quality:
        return "İzle", ["Fiyat trendi olumlu.", "Temel kalite verisi bu taramada alınamadı."]

    margin = quality["margin"]
    roe = quality["roe"]
    debt = quality["debt_to_equity"]
    cashflow = quality["operating_cashflow"]
    quality_ok = (
        margin is not None and margin > 0
        and roe is not None and roe > 0.10
        and debt is not None and debt <= 150
        and cashflow is not None and cashflow > 0
    )
    reasons = [f"20 günlük fiyat değişimi {item['return_20d']:+.1f}% ve fiyat 20 günlük ortalamanın üzerinde."]
    if quality_ok:
        reasons.append(f"Net marj {margin * 100:.1f}%, ROE {roe * 100:.1f}% ve işletme nakit akımı pozitif.")
        reasons.append(f"Borç/özkaynak {debt:.1f} seviyesinde.")
        return "Araştırmaya değer", reasons

    missing = []
    if margin is None or margin <= 0:
        missing.append("kârlılık")
    if roe is None or roe <= 0.10:
        missing.append("ROE")
    if debt is None or debt > 150:
        missing.append("borç")
    if cashflow is None or cashflow <= 0:
        missing.append("işletme nakit akımı")
    reasons.append("Teyit gerektiren başlıklar: " + ", ".join(missing) + ".")
    return "İzle", reasons


def main() -> None:
    print("ABD büyük ölçekli hisse evreni taranıyor...")
    prices = yf.download(US_LARGE_CAP, period="3mo", auto_adjust=True, group_by="ticker", progress=False, threads=True)
    items = []
    for symbol in US_LARGE_CAP:
        try:
            closes = prices[symbol]["Close"].dropna()
            if len(closes) < 21:
                continue
            last = float(closes.iloc[-1])
            item = {
                "symbol": symbol,
                "last_price": last,
                "return_20d": (last / float(closes.iloc[-21]) - 1) * 100,
                "distance_sma20": (last / float(closes.tail(20).mean()) - 1) * 100,
            }
            items.append(item)
        except (KeyError, IndexError):
            continue

    candidates = [item for item in items if item["return_20d"] > 0 and item["distance_sma20"] > 0]
    print("Olumlu trendli şirketlerin temel kalite verileri inceleniyor...")
    # yfinance'ın yerel önbelleği eşzamanlı bilgi isteklerinde kilitlenebiliyor.
    # Fiyatlar zaten toplu alındığı için bu kısa ikinci adımı sıralı yapmak daha güvenilir.
    for item in candidates:
        try:
            item["quality"] = get_quality(item["symbol"])
        except Exception:
            item["quality"] = None

    order = {"Araştırmaya değer": 0, "İzle": 1, "Dikkat": 2}
    for item in items:
        item["status"], item["reasons"] = classify(item)
    items.sort(key=lambda item: (order[item["status"]], -item["return_20d"]))

    rows = ""
    for item in items:
        quality = item.get("quality") or {}
        status_class = {"Araştırmaya değer": "research", "İzle": "watch", "Dikkat": "caution"}[item["status"]]
        margin = number(quality.get("margin"))
        roe = number(quality.get("roe"))
        pe = number(quality.get("pe"))
        rows += f"""<tr><td><span class="tag {status_class}">{item['status']}</span></td><td><strong>{item['symbol']}</strong></td><td>{html.escape(str(quality.get('name') or '—'))}</td><td>${item['last_price']:,.2f}</td><td>{item['return_20d']:+.1f}%</td><td>{'—' if margin is None else f'{margin * 100:.1f}%'}</td><td>{'—' if roe is None else f'{roe * 100:.1f}%'}</td><td>{'—' if pe is None else f'{pe:.1f}'}</td><td>{html.escape(' · '.join(item['reasons']))}</td></tr>"""

    counts = {name: sum(1 for item in items if item["status"] == name) for name in order}
    report = f"""<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>ABD Piyasaları Fırsat Tarama | BIST Radar</title><style>
body{{margin:0;background:#f4f7fa;color:#18212f;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}main{{max-width:1480px;margin:auto;padding:42px 22px 64px}}h1{{margin:0;font-size:38px}}.sub{{color:#63748a;margin:8px 0 22px;line-height:1.45}}.summary{{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:18px}}.summary div{{background:white;border:1px solid #e1e7ef;border-radius:12px;padding:12px 16px;font-weight:700}}.table{{overflow-x:auto;background:white;border:1px solid #e1e7ef;border-radius:14px}}table{{width:100%;border-collapse:collapse;min-width:1250px}}th,td{{padding:14px 15px;text-align:left;border-bottom:1px solid #edf1f5}}th{{background:#f8fafc;color:#586b83;font-size:12px;text-transform:uppercase}}tr:last-child td{{border-bottom:0}}td:last-child{{color:#516175;font-size:13px;line-height:1.4}}.tag{{font-size:13px;font-weight:750;padding:6px 9px;border-radius:999px;white-space:nowrap}}.research{{color:#087a46;background:#d9f6e7}}.watch{{color:#985e04;background:#fff1d6}}.caution{{color:#b4233a;background:#fde8eb}}footer{{color:#63748a;font-size:13px;margin-top:18px}}
</style></head><body><main><h1>ABD Piyasaları Fırsat Tarama</h1><p class="sub">{datetime.now().strftime('%d.%m.%Y %H:%M')} · Yaklaşık 40 büyük ve likit ABD şirketi · Araştırma önceliği filtresi, yatırım tavsiyesi değildir.</p><div class="summary"><div>{len(items)} şirket tarandı</div><div>{counts['Araştırmaya değer']} araştırmaya değer</div><div>{counts['İzle']} izle</div><div>{counts['Dikkat']} dikkat</div></div><div class="table"><table><thead><tr><th>Durum</th><th>Kod</th><th>Şirket</th><th>Son fiyat</th><th>20 gün</th><th>Net marj</th><th>ROE</th><th>F/K</th><th>Neden?</th></tr></thead><tbody>{rows}</tbody></table></div><footer>“Araştırmaya değer”: 20 günlük trend pozitif, fiyat 20 günlük ortalamanın üzerinde, net marj pozitif, ROE %10 üzerinde, borç/özkaynak ≤ 150 ve işletme nakit akımı pozitif. Bu kurallar sadece ilk filtreleme içindir; değerleme, sektör, haberler, bilanço kalitesi ve kişisel risk ayrıca incelenmelidir.</footer></main></body></html>"""
    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"abd-firsat-tarama-{datetime.now().strftime('%Y-%m-%d')}.html"
    output_file.write_text(report, encoding="utf-8")
    print(f"ABD fırsat tarama raporu oluşturuldu: {output_file}")
    if not os.environ.get("BIST_RADAR_NO_BROWSER"):
        webbrowser.open(output_file.resolve().as_uri())


if __name__ == "__main__":
    main()
