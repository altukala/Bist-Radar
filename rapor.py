"""Bir hisse için tarayıcıda açılan, okunabilir HTML raporu üretir."""

import html
import os
import sys
import webbrowser
from datetime import date
from pathlib import Path

import certifi

os.environ.setdefault("SSL_CERT_FILE", certifi.where())

from analiz import get_quality
from radar import analyze_stock


def percent(value: float) -> str:
    return f"{value:+.1f}%"


def main() -> None:
    symbol = sys.argv[1].upper() if len(sys.argv) > 1 else "THYAO"
    trend = analyze_stock(symbol)
    quality = get_quality(symbol)

    warnings: list[str] = []
    if trend["return_20d"] < 0 and trend["return_5d"] < 0:
        warnings.append("Kısa ve orta vadeli fiyat momentumu birlikte negatif.")
    if trend["return_20d"] > 0 and trend["return_5d"] < 0:
        warnings.append("Orta vadeli yükseliş sürse de son günlerde geri çekilme var.")
    if quality["net_debt_to_equity"] > 100:
        warnings.append("Net borç/özkaynak %100'ün üzerinde; borç riski ayrıca incelenmeli.")
    if "yüksek oynaklık" in trend["reasons"][-1]:
        warnings.append("Fiyat oynaklığı yüksek; pozisyon büyüklüğü ve zamanlama riski artar.")
    if quality["operating_cash"] < 0:
        warnings.append("Faaliyetlerden nakit çıkışı var.")
    if not warnings:
        warnings.append("Bu basit ölçütlerde belirgin bir kırmızı bayrak oluşmadı.")

    reason_items = "".join(f"<li>{html.escape(reason)}</li>" for reason in trend["reasons"])
    warning_items = "".join(f"<li>{html.escape(warning)}</li>" for warning in warnings)

    report = f"""<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{symbol} | BIST Radar</title>
  <style>
    body {{ margin: 0; background: #f5f7fa; color: #18212f; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    main {{ max-width: 900px; margin: auto; padding: 44px 22px 64px; }}
    .eyebrow {{ color: #62748a; font-size: 14px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }}
    h1 {{ font-size: 42px; margin: 8px 0; }}
    .note {{ color: #62748a; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 14px; margin: 28px 0; }}
    .card {{ background: white; border: 1px solid #e1e7ef; border-radius: 16px; padding: 20px; box-shadow: 0 2px 6px #1a263010; }}
    .label {{ color: #62748a; font-size: 13px; font-weight: 700; text-transform: uppercase; }}
    .value {{ font-size: 27px; font-weight: 750; margin-top: 8px; }}
    section {{ background: white; border: 1px solid #e1e7ef; border-radius: 16px; padding: 22px; margin-top: 16px; }}
    h2 {{ margin: 0 0 14px; font-size: 19px; }}
    li {{ margin: 9px 0; line-height: 1.45; }}
    .positive {{ color: #087a46; }} .negative {{ color: #bb2d3b; }} .neutral {{ color: #9b6510; }}
    footer {{ color: #62748a; font-size: 13px; margin-top: 22px; }}
  </style>
</head>
<body><main>
  <div class="eyebrow">BIST Radar · {date.today().isoformat()}</div>
  <h1>{symbol} Analiz Özeti</h1>
  <p class="note">Bilgi amaçlıdır; yatırım tavsiyesi veya al/sat emri değildir.</p>
  <div class="grid">
    <div class="card"><div class="label">Fiyat görünümü</div><div class="value">{html.escape(str(trend['trend']))}</div></div>
    <div class="card"><div class="label">20 günlük değişim</div><div class="value">{percent(float(trend['return_20d']))}</div></div>
    <div class="card"><div class="label">Net kâr marjı</div><div class="value">{float(quality['net_margin']):.1f}%</div></div>
    <div class="card"><div class="label">Net borç / özkaynak</div><div class="value">{float(quality['net_debt_to_equity']):.1f}%</div></div>
  </div>
  <section><h2>Fiyat trendinin nedenleri</h2><ul>{reason_items}</ul></section>
  <section><h2>Şirket kalitesi ({quality['year']})</h2><ul>
    <li>Satış büyümesi: {percent(float(quality['revenue_growth']))}</li>
    <li>Özkaynak kârlılığı: {float(quality['roe']):.1f}%</li>
    <li>İşletme nakit akımı: {"pozitif" if quality['operating_cash'] > 0 else "negatif"}</li>
  </ul></section>
  <section><h2>Dikkat noktaları</h2><ul>{warning_items}</ul></section>
  <footer>Karar vermeden önce güncel KAP açıklamalarını, bilanço dipnotlarını ve kendi riskini ayrıca değerlendir.</footer>
</main></body></html>"""

    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"{symbol}-{date.today().isoformat()}.html"
    output_file.write_text(report, encoding="utf-8")
    print(f"Rapor oluşturuldu: {output_file}")
    webbrowser.open(output_file.resolve().as_uri())


if __name__ == "__main__":
    main()
