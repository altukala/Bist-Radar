"""Bir BIST hissesi için trend, finansal kalite ve risk özetini birleştirir."""

import os
import sys

import certifi

os.environ.setdefault("SSL_CERT_FILE", certifi.where())

import borsapy as bp
from kalite import sum_values, value
from radar import analyze_stock


def get_quality(symbol: str) -> dict[str, float | int]:
    stock = bp.Ticker(symbol)
    income = stock.income_stmt
    balance = stock.balance_sheet
    cashflow = stock.cashflow
    current_year, previous_year = income.columns[:2]

    revenue = value(income, "Satış Gelirleri", current_year)
    previous_revenue = value(income, "Satış Gelirleri", previous_year)
    net_income = value(income, "DÖNEM KARI (ZARARI)", current_year)
    equity = value(balance, "Özkaynaklar", current_year)
    cash = value(balance, "Nakit ve Nakit Benzerleri", current_year)
    debt = sum_values(balance, "Finansal Borçlar", current_year)
    operating_cash = value(cashflow, "İşletme Faaliyetlerinden Kaynaklanan Net Nakit", current_year)

    return {
        "year": current_year,
        "revenue_growth": (revenue / previous_revenue - 1) * 100,
        "net_margin": net_income / revenue * 100,
        "roe": net_income / equity * 100,
        "net_debt_to_equity": (debt - cash) / equity * 100,
        "operating_cash": operating_cash,
    }


def main() -> None:
    symbol = sys.argv[1].upper() if len(sys.argv) > 1 else "THYAO"
    trend = analyze_stock(symbol)
    quality = get_quality(symbol)

    print(f"\n{symbol} — Birleşik Hisse Analizi")
    print("Bu çıktı bilgi amaçlıdır; yatırım tavsiyesi veya al/sat emri değildir.\n")

    print("FİYAT TRENDİ")
    print(f"Görünüm: {trend['trend']}")
    for reason in trend["reasons"]:
        print(f"- {reason}")

    print(f"\nŞİRKET KALİTESİ ({quality['year']})")
    print(f"- Satış büyümesi: {quality['revenue_growth']:+.1f}%")
    print(f"- Net kâr marjı: {quality['net_margin']:.1f}%")
    print(f"- Özkaynak kârlılığı: {quality['roe']:.1f}%")
    print(f"- Net borç / özkaynak: {quality['net_debt_to_equity']:.1f}%")
    print(
        "- İşletme nakit akımı: "
        + ("pozitif" if quality["operating_cash"] > 0 else "negatif")
    )

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

    print("\nDİKKAT NOKTALARI")
    if warnings:
        for warning in warnings:
            print(f"- {warning}")
    else:
        print("- Bu basit ölçütlerde belirgin bir kırmızı bayrak oluşmadı.")

    print("\nKarar vermeden önce güncel KAP açıklamalarını, bilanço dipnotlarını ve kişisel riskini ayrıca değerlendir.")


if __name__ == "__main__":
    main()
