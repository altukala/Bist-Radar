"""BIST30 içinde şeffaf kurallarla araştırma önceliği listesi oluşturur."""

import html
import os
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import certifi

os.environ.setdefault("SSL_CERT_FILE", certifi.where())

import borsapy as bp
from analiz import get_quality
from radar import analyze_stock


def classify(trend: dict[str, object], quality: dict[str, float | int] | None) -> tuple[str, list[str]]:
    """Al/sat önerisi vermeden, kuralları görünür bir filtreye dönüştürür."""
    positive_trend = str(trend["trend"]) in {"Güçlü pozitif", "Pozitif"}
    if not positive_trend:
        return "Dikkat", [
            f"20 günlük fiyat değişimi {float(trend['return_20d']):+.1f}%.",
            "Fiyat trendi henüz olumlu teyit vermiyor.",
        ]
    if quality is None:
        return "İzle", ["Fiyat trendi olumlu.", "Finansal kalite verisi bu taramada alınamadı."]

    checks = {
        "Satış büyümesi": float(quality["revenue_growth"]) > 0,
        "Net kâr marjı": float(quality["net_margin"]) > 0,
        "Net borç/özkaynak": float(quality["net_debt_to_equity"]) <= 100,
        "İşletme nakit akımı": float(quality["operating_cash"]) > 0,
    }
    reasons = [f"20 günlük fiyat değişimi {float(trend['return_20d']):+.1f}%."]
    if all(checks.values()):
        reasons.extend([
            f"Satış büyümesi {float(quality['revenue_growth']):+.1f}% ve net kâr marjı {float(quality['net_margin']):.1f}%.",
            f"Net borç/özkaynak {float(quality['net_debt_to_equity']):.1f}% ve işletme nakit akımı pozitif.",
        ])
        return "Araştırmaya değer", reasons

    failed = [name for name, passed in checks.items() if not passed]
    reasons.append("Teyit gerektiren başlıklar: " + ", ".join(failed) + ".")
    return "İzle", reasons


def main() -> None:
    symbols = bp.Index("XU030").component_symbols
    trends: list[dict[str, object]] = []
    print("BIST30 fiyat trendleri taranıyor...")
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(analyze_stock, symbol): symbol for symbol in symbols}
        for future in as_completed(futures):
            try:
                trends.append(future.result())
            except Exception:
                pass

    positive = [item for item in trends if str(item["trend"]) in {"Güçlü pozitif", "Pozitif"}]
    qualities: dict[str, dict[str, float | int]] = {}
    print("Olumlu trendli hisselerin temel finansalları inceleniyor...")
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(get_quality, str(item["symbol"])): str(item["symbol"]) for item in positive}
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                qualities[symbol] = future.result()
            except Exception:
                pass

    order = {"Araştırmaya değer": 0, "İzle": 1, "Dikkat": 2}
    items = []
    for trend in trends:
        quality = qualities.get(str(trend["symbol"]))
        status, reasons = classify(trend, quality)
        items.append({"trend": trend, "quality": quality, "status": status, "reasons": reasons})
    items.sort(key=lambda item: (order[item["status"]], -float(item["trend"]["return_20d"])))

    rows = ""
    for item in items:
        trend, quality, status = item["trend"], item["quality"], item["status"]
        css = {"Araştırmaya değer": "research", "İzle": "watch", "Dikkat": "caution"}[status]
        margin = f"{float(quality['net_margin']):.1f}%" if quality else "—"
        debt = f"{float(quality['net_debt_to_equity']):.1f}%" if quality else "—"
        reasons = " · ".join(item["reasons"])
        rows += f"""<tr><td><span class="tag {css}">{status}</span></td><td><strong>{html.escape(str(trend['symbol']))}</strong></td><td>{float(trend['return_20d']):+.1f}%</td><td>{margin}</td><td>{debt}</td><td>{html.escape(reasons)}</td></tr>"""

    counts = {name: sum(1 for item in items if item["status"] == name) for name in order}
    report = f"""<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>BIST30 Fırsat Tarama | BIST Radar</title><style>
body{{margin:0;background:#f4f7fa;color:#18212f;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}main{{max-width:1200px;margin:auto;padding:42px 22px 64px}}h1{{margin:0;font-size:38px}}.sub{{color:#63748a;margin:8px 0 22px;line-height:1.45}}.summary{{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:18px}}.summary div{{background:white;border:1px solid #e1e7ef;border-radius:12px;padding:12px 16px;font-weight:700}}.table{{overflow-x:auto;background:white;border:1px solid #e1e7ef;border-radius:14px}}table{{width:100%;border-collapse:collapse;min-width:920px}}th,td{{padding:14px 15px;text-align:left;border-bottom:1px solid #edf1f5}}th{{background:#f8fafc;color:#586b83;font-size:12px;text-transform:uppercase}}tr:last-child td{{border-bottom:0}}td:last-child{{color:#516175;font-size:13px;line-height:1.4}}.tag{{font-size:13px;font-weight:750;padding:6px 9px;border-radius:999px;white-space:nowrap}}.research{{color:#087a46;background:#d9f6e7}}.watch{{color:#985e04;background:#fff1d6}}.caution{{color:#b4233a;background:#fde8eb}}footer{{color:#63748a;font-size:13px;margin-top:18px}}
</style></head><body><main><h1>BIST30 Fırsat Tarama</h1><p class="sub">{datetime.now().strftime('%d.%m.%Y %H:%M')} · Bu liste araştırma önceliği filtresidir; al/sat tavsiyesi değildir.</p><div class="summary"><div>{counts['Araştırmaya değer']} araştırmaya değer</div><div>{counts['İzle']} izle</div><div>{counts['Dikkat']} dikkat</div></div><div class="table"><table><thead><tr><th>Durum</th><th>Hisse</th><th>20 gün</th><th>Net marj</th><th>Net borç/özk.</th><th>Neden?</th></tr></thead><tbody>{rows}</tbody></table></div><footer>“Araştırmaya değer” etiketi: olumlu fiyat trendi, pozitif satış büyümesi, pozitif net kâr marjı, pozitif işletme nakit akımı ve net borç/özkaynak ≤ %100 koşullarının birlikte sağlandığını belirtir. Sektör farkları, güncel KAP açıklamaları ve kişisel risk ayrıca incelenmelidir.</footer></main></body></html>"""

    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"firsat-tarama-{datetime.now().strftime('%Y-%m-%d')}.html"
    output_file.write_text(report, encoding="utf-8")
    print(f"Fırsat tarama raporu oluşturuldu: {output_file}")
    if not os.environ.get("BIST_RADAR_NO_BROWSER"):
        webbrowser.open(output_file.resolve().as_uri())


if __name__ == "__main__":
    main()
