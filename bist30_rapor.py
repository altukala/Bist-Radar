"""BIST30 trend taramasını tarayıcıda okunabilir bir tablo olarak gösterir."""

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


def trend_class(trend: str) -> str:
    return {
        "Güçlü pozitif": "strong",
        "Pozitif": "positive",
        "Negatif": "negative",
    }.get(trend, "mixed")


def main() -> None:
    symbols = bp.Index("XU030").component_symbols
    results: list[dict[str, object]] = []
    failures: list[str] = []
    print("BIST30 verileri alınıyor; bu işlem yaklaşık yarım dakika sürebilir...")

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(analyze_stock, symbol): symbol for symbol in symbols}
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                results.append(future.result())
            except Exception as error:
                failures.append(f"{symbol}: {error}")

    print("Şirketlerin temel finansal kalite verileri inceleniyor...")
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(get_quality, str(item["symbol"])): item for item in results}
        for future in as_completed(futures):
            item = futures[future]
            try:
                item["quality"] = future.result()
            except Exception:
                item["quality"] = None

    results.sort(key=lambda item: float(item["return_20d"]), reverse=True)
    rows = ""
    for item in results:
        quality = item.get("quality") or {}
        reasons = " · ".join(str(reason) for reason in item["reasons"])
        rows += f"""<tr data-trend="{trend_class(str(item['trend']))}">
<td><strong>{html.escape(str(item['symbol']))}</strong></td>
<td>{float(item['last_price']):,.2f} TL</td>
<td class="{'up' if item['return_5d'] >= 0 else 'down'}">{float(item['return_5d']):+.1f}%</td>
<td class="{'up' if item['return_20d'] >= 0 else 'down'}">{float(item['return_20d']):+.1f}%</td>
<td>{float(item['distance_sma20']):+.1f}%</td>
<td>{float(item['annualized_volatility']):.0f}%</td>
<td>{'—' if not quality else f"{float(quality['revenue_growth']):+.1f}%"}</td>
<td>{'—' if not quality else f"{float(quality['net_margin']):.1f}%"}</td>
<td>{'—' if not quality else f"{float(quality['roe']):.1f}%"}</td>
<td>{'—' if not quality else f"{float(quality['net_debt_to_equity']):.1f}%"}</td>
<td>{'—' if not quality else ('Pozitif' if float(quality['operating_cash']) > 0 else 'Negatif')}</td>
<td><span class="tag {trend_class(str(item['trend']))}">{html.escape(str(item['trend']))}</span></td>
<td class="reason">{html.escape(reasons)}</td>
</tr>"""

    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    report = f"""<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>BIST30 Genel Görünüm | BIST Radar</title>
<style>
body {{ margin:0; background:#f4f7fa; color:#18212f; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }}
main {{ max-width:1640px; margin:auto; padding:42px 22px 64px; }}
h1 {{ margin:0; font-size:38px; }} .subtitle {{ color:#63748a; margin:8px 0 26px; }}
.summary {{ display:flex; flex-wrap:wrap; gap:10px; margin:0 0 18px; }}
.summary div {{ background:white; border:1px solid #e1e7ef; padding:12px 16px; border-radius:12px; font-weight:650; }}
input {{ width:100%; box-sizing:border-box; padding:13px 15px; border:1px solid #cbd6e2; border-radius:10px; font-size:16px; margin:0 0 16px; }}
.table-wrap {{ overflow-x:auto; background:white; border:1px solid #e1e7ef; border-radius:14px; }}
table {{ width:100%; border-collapse:collapse; min-width:1600px; }} th,td {{ padding:14px 15px; text-align:left; border-bottom:1px solid #edf1f5; }}
th {{ background:#f8fafc; color:#586b83; font-size:12px; text-transform:uppercase; letter-spacing:.05em; }}
tr:last-child td {{ border-bottom:0; }} .up {{ color:#087a46; font-weight:700; }} .down {{ color:#b4233a; font-weight:700; }}
.tag {{ padding:5px 9px; border-radius:999px; font-size:13px; font-weight:700; white-space:nowrap; }}
.strong {{ background:#d9f6e7; color:#087a46; }} .positive {{ background:#e5f2ff; color:#176aa3; }} .negative {{ background:#fde8eb; color:#b4233a; }} .mixed {{ background:#fff1d6; color:#985e04; }}
.reason {{ color:#516175; font-size:13px; line-height:1.4; }} footer {{ color:#63748a; font-size:13px; margin-top:18px; }}
</style></head><body><main>
<h1>BIST30 Genel Görünüm</h1><p class="subtitle">{now} · Fiyat trendi ve temel finansal kalite bazlı günlük tarama · Yatırım tavsiyesi değildir.</p>
<div class="summary"><div>{len(results)} hisse tarandı</div><div>{sum(1 for x in results if x['trend'] == 'Güçlü pozitif')} güçlü pozitif</div><div>{sum(1 for x in results if x['trend'] == 'Negatif')} negatif</div></div>
<input id="search" type="search" placeholder="Hisse kodu veya trend ara (örnek: THYAO, negatif)">
<div class="table-wrap"><table><thead><tr><th>Hisse</th><th>Son fiyat</th><th>5 gün</th><th>20 gün</th><th>20 GO uzaklık</th><th>Oynaklık</th><th>Satış büyümesi</th><th>Net marj</th><th>ROE</th><th>Net borç/özk.</th><th>Nakit akımı</th><th>Görünüm</th><th>Neden?</th></tr></thead><tbody id="rows">{rows}</tbody></table></div>
<footer>Fiyat ölçütleri son üç aylık harekete; finansal ölçütler en son yıllık mali tablolara dayanır. Renkler yatırım tavsiyesi değil, fiyat trendi özetidir. KAP açıklamaları, sektör farkları ve kişisel risk ayrıca değerlendirilmelidir.</footer>
</main><script>
const search=document.getElementById('search');
search.addEventListener('input',()=>{{const q=search.value.toLocaleLowerCase('tr');document.querySelectorAll('#rows tr').forEach(row=>{{row.hidden=!row.textContent.toLocaleLowerCase('tr').includes(q)}})}});
</script></body></html>"""

    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"BIST30-{datetime.now().strftime('%Y-%m-%d')}.html"
    output_file.write_text(report, encoding="utf-8")
    print(f"Rapor oluşturuldu: {output_file} ({len(results)}/{len(symbols)} hisse)")
    if failures:
        print(f"Alınamayan veri sayısı: {len(failures)}")
    if not os.environ.get("BIST_RADAR_NO_BROWSER"):
        webbrowser.open(output_file.resolve().as_uri())


if __name__ == "__main__":
    main()
