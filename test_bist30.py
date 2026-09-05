import borsapy as bp


def main() -> None:
    bist30 = bp.Index("XU030")
    components = bist30.components

    print(f"Endeks: BIST 30 ({bist30.symbol})")
    print(f"Alınan hisse sayısı: {len(components)}")
    print("İlk beş hisse:")
    for company in components[:5]:
        print(f"- {company['symbol']}: {company['name']}")

    if len(components) < 25:
        raise RuntimeError("BIST30 bileşenleri beklenen sayıda alınamadı.")


if __name__ == "__main__":
    main()
