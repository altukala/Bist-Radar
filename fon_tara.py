"""TEFAS yatırım fonları için getirileri görünür bir araştırma ekranı oluşturur."""

import html
import os
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import certifi

os.environ.setdefault("SSL_CERT_FILE", certifi.where())

import borsapy as bp


def number(item: dict, key: str) -> float | None:
    value = item.get(key)
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def text_percent(value: float | None) -> str:
    return "—" if value is None else f"{value:+.1f}%"


def text_money(value: float | None) -> str:
    if value is None:
        return "—"
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f} mlr TL"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f} mn TL"
    return f"{value:,.0f} TL"


def get_detail(fund_code: str) -> dict[str, float | str | None]:
    info = bp.Fund(fund_code).info
    return {
        "price": number(info, "price"),
        "fund_size": number(info, "fund_size"),
        "investor_count": number(info, "investor_count"),
        "risk_value": number(info, "risk_value"),
        "category": info.get("category"),
    }


def classify(fund: dict) -> tuple[str, str]:
    r1m, r3m, rytd = (number(fund, key) for key in ("return_1m", "return_3m", "return_ytd"))
    if all(value is not None and value > 0 for value in (r1m, r3m, rytd)):
        return "Araştırmaya değer", "1 ay, 3 ay ve yılbaşından beri getiri pozitif."
    if rytd is not None and rytd > 0:
        return "İzle", "Yılbaşından beri getiri pozitif; kısa vadeli seyir teyit gerektiriyor."
    return "Dikkat", "Getiri pencerelerinin en az biri negatif veya veri eksik."


def main() -> None:
    print("TEFAS yatırım fonları taranıyor...")
    funds = bp.screen_funds(fund_type="YAT", limit=50).to_dict("records")
    order = {"Araştırmaya değer": 0, "İzle": 1, "Dikkat": 2}
    items = []
    for fund in funds:
        status, reason = classify(fund)
        items.append({"fund": fund, "status": status, "reason": reason})
    items.sort(key=lambda item: (order[item["status"]], -(number(item["fund"], "return_1y") or -999999)))

    print("Araştırma önceliği yüksek fonların ayrıntıları alınıyor...")
    detail_targets = items[:20]
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(get_detail, item["fund"]["fund_code"]): item for item in detail_targets}
        for future in as_completed(futures):
            item = futures[future]
            try:
                item["detail"] = future.result()
            except Exception:
                item["detail"] = {}

    fees: dict[str, float | None] = {}
    try:
        fee_table = bp.management_fees(fund_type="YAT")
        fees = {str(row["fund_code"]): number(row, "applied_fee") for _, row in fee_table.iterrows()}
    except Exception:
        pass

    rows = ""
    for item in items:
        fund, status = item["fund"], item["status"]
        detail = item.get("detail") or {}
        css = {"Araştırmaya değer": "research", "İzle": "watch", "Dikkat": "caution"}[status]
        fee = fees.get(str(fund.get("fund_code")))
        rows += f"""<tr><td><span class="tag {css}">{status}</span></td><td><strong>{html.escape(str(fund.get('fund_code', '')))}</strong></td><td>{html.escape(str(fund.get('name', '')))}</td><td>{html.escape(str(detail.get('category') or fund.get('fund_type', '')))}</td><td>{'—' if detail.get('price') is None else f"{detail['price']:.4f}"}</td><td>{text_percent(number(fund, 'return_1m'))}</td><td>{text_percent(number(fund, 'return_3m'))}</td><td>{text_percent(number(fund, 'return_6m'))}</td><td>{text_percent(number(fund, 'return_ytd'))}</td><td>{text_percent(number(fund, 'return_1y'))}</td><td>{'—' if detail.get('risk_value') is None else f"{detail['risk_value']:.0f}/7"}</td><td>{text_money(detail.get('fund_size'))}</td><td>{'—' if detail.get('investor_count') is None else f"{detail['investor_count']:,.0f}"}</td><td>{'—' if fee is None else f"{fee:.2f}%"}</td><td>{item['reason']}</td></tr>"""

    counts = {status: sum(1 for item in items if item["status"] == status) for status in order}
    report = f"""<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>TEFAS Fon Tarama | BIST Radar</title><style>
body{{margin:0;background:#f4f7fa;color:#18212f;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}main{{max-width:1880px;margin:auto;padding:42px 22px 64px}}h1{{margin:0;font-size:38px}}.sub{{color:#63748a;margin:8px 0 22px;line-height:1.45}}.summary{{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:18px}}.summary div{{background:white;border:1px solid #e1e7ef;border-radius:12px;padding:12px 16px;font-weight:700}}.table{{overflow-x:auto;background:white;border:1px solid #e1e7ef;border-radius:14px}}table{{width:100%;border-collapse:collapse;min-width:1880px}}th,td{{padding:14px 15px;text-align:left;border-bottom:1px solid #edf1f5}}th{{background:#f8fafc;color:#586b83;font-size:12px;text-transform:uppercase}}tr:last-child td{{border-bottom:0}}td:last-child{{color:#516175;font-size:13px;line-height:1.4}}.tag{{font-size:13px;font-weight:750;padding:6px 9px;border-radius:999px;white-space:nowrap}}.research{{color:#087a46;background:#d9f6e7}}.watch{{color:#985e04;background:#fff1d6}}.caution{{color:#b4233a;background:#fde8eb}}footer{{color:#63748a;font-size:13px;margin-top:18px}}
</style></head><body><main><h1>TEFAS Fon Tarama</h1><p class="sub">{datetime.now().strftime('%d.%m.%Y %H:%M')} · İlk 50 yatırım fonu, 1 yıllık getiriye göre sıralanır. Bu liste yatırım tavsiyesi değildir.</p><div class="summary"><div>{counts['Araştırmaya değer']} araştırmaya değer</div><div>{counts['İzle']} izle</div><div>{counts['Dikkat']} dikkat</div></div><div class="table"><table><thead><tr><th>Durum</th><th>Kod</th><th>Fon</th><th>Tür</th><th>Fiyat</th><th>1 ay</th><th>3 ay</th><th>6 ay</th><th>YBB</th><th>1 yıl</th><th>Risk</th><th>Fon büyüklüğü</th><th>Yatırımcı</th><th>Yönetim ücreti</th><th>Neden?</th></tr></thead><tbody>{rows}</tbody></table></div><footer>Risk değeri, fon büyüklüğü ve yatırımcı sayısı araştırma önceliği en yüksek ilk 20 fon için alınır; diğer satırlarda veri sağlayıcı yükünü azaltmak için boş kalabilir. “Araştırmaya değer” etiketi yalnızca 1 ay, 3 ay ve yılbaşından beri getirinin birlikte pozitif olduğunu belirtir. Geçmiş getiri gelecekteki getiriyi garanti etmez.</footer></main></body></html>"""
    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"tefas-fon-tarama-{datetime.now().strftime('%Y-%m-%d')}.html"
    output_file.write_text(report, encoding="utf-8")
    print(f"TEFAS fon raporu oluşturuldu: {output_file}")
    if not os.environ.get("BIST_RADAR_NO_BROWSER"):
        webbrowser.open(output_file.resolve().as_uri())


if __name__ == "__main__":
    main()
