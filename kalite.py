"""Bir BIST şirketinin temel finansal kalite özetini gösterir."""

import os
import sys

import certifi

os.environ.setdefault("SSL_CERT_FILE", certifi.where())

import borsapy as bp


def value(frame, label: str, year) -> float:
    """Başındaki boşluklar farklı olabilen finansal tablo satırını bulur."""
    row = next(item for item in frame.index if item.strip() == label)
    return float(frame.loc[row, year])


def sum_values(frame, label: str, year) -> float:
    return sum(
        float(frame.iloc[position][year])
        for position, item in enumerate(frame.index)
        if item.strip() == label
    )


def billion(value_in_tl: float) -> str:
    return f"{value_in_tl / 1_000_000_000:,.1f} mlr TL"


def main() -> None:
    symbol = sys.argv[1].upper() if len(sys.argv) > 1 else "THYAO"
    stock = bp.Ticker(symbol)
    income = stock.income_stmt
    balance = stock.balance_sheet
    cashflow = stock.cashflow
    current_year, previous_year = income.columns[:2]

    revenue = value(income, "Satış Gelirleri", current_year)
    previous_revenue = value(income, "Satış Gelirleri", previous_year)
    net_income = value(income, "DÖNEM KARI (ZARARI)", current_year)
    operating_income = value(income, "FAALİYET KARI (ZARARI)", current_year)
    equity = value(balance, "Özkaynaklar", current_year)
    cash = value(balance, "Nakit ve Nakit Benzerleri", current_year)
    financial_debt = sum_values(balance, "Finansal Borçlar", current_year)
    operating_cash = value(cashflow, "İşletme Faaliyetlerinden Kaynaklanan Net Nakit", current_year)

    revenue_growth = (revenue / previous_revenue - 1) * 100
    net_margin = net_income / revenue * 100
    operating_margin = operating_income / revenue * 100
    roe = net_income / equity * 100
    net_debt = financial_debt - cash
    net_debt_to_equity = net_debt / equity * 100

    print(f"\n{symbol} — Şirket Kalitesi Özeti ({current_year})")
    print("Bu ekran finansal veriyi açıklar; yatırım tavsiyesi değildir.\n")
    print(f"Satış geliri:         {billion(revenue)}  (önceki yıla göre {revenue_growth:+.1f}%)")
    print(f"Dönem kârı:           {billion(net_income)}  (net kâr marjı {net_margin:.1f}%)")
    print(f"Faaliyet kâr marjı:   {operating_margin:.1f}%")
    print(f"Özkaynak kârlılığı:   {roe:.1f}%")
    print(f"Net borç / özkaynak:  {net_debt_to_equity:.1f}%")
    print(f"İşletme nakit akımı:  {billion(operating_cash)}")

    print("\nYorumlar:")
    print("- " + ("Satışlar yıllık bazda büyümüş." if revenue_growth > 0 else "Satışlar yıllık bazda daralmış."))
    print("- " + ("Şirket bu dönemi kârla kapatmış." if net_income > 0 else "Şirket bu dönemi zararla kapatmış."))
    print("- " + ("Faaliyetlerden pozitif nakit üretilmiş." if operating_cash > 0 else "Faaliyetlerden nakit çıkışı olmuş."))
    if net_debt < 0:
        print("- Nakit, finansal borçların üzerinde (net nakit pozisyonu).")
    elif net_debt_to_equity > 100:
        print("- Net borç, özkaynağa göre yüksek; borç riski ayrıca incelenmeli.")
    else:
        print("- Borç özkaynağa göre yönetilebilir seviyede görünüyor.")


if __name__ == "__main__":
    main()
