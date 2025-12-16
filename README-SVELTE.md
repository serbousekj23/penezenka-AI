# Svelte Crypto Wallet (demo)

Jednoduchá demo krypto peněženka vytvořená ve `Svelte` + `Vite`.

Poznámka: Toto je ukázkový projekt — NEPOUŽÍVEJTE s reálnými prostředky bez bezpečnostních auditů.

Rychlý start (PowerShell / Windows):

```powershell
npm install
npm run dev
```

Otevřete v prohlížeči: `http://localhost:5173`

Funkce:
- Generování nové peněženky (mnemonic + private key)
- Import pomocí private key nebo mnemonic
- Načtení ETH zůstatku z veřejného provideru (default provider)
 - Zobrazení tržních cen (ETH, BTC, USDC) a přepočet ETH zůstatku na USD (CoinGecko)
 - Lokální přihlášení/registrace: přístup k peněžence je možný jen po přihlášení (demo, hash hesla ukládán v localStorage)

Další kroky:
- Přidat šifrování seedů v lokálním úložišti
- Přidat transakční podpůrné funkce a bezpečnostní prvky
