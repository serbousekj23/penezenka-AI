<script>
  import { onMount } from 'svelte';
  import { Wallet, getDefaultProvider } from 'ethers';

  let address = '';
  let privateKey = '';
  let mnemonic = '';
  let balance = null;
  let balanceUSD = null;
  let network = 'homestead';
  let error = '';
  let provider = null;

  // Prices fetched from CoinGecko
  let prices = {};
  let pricesLast = null;

  let importKeyInput = '';
  let importMnemonicInput = '';
  let showPrivate = false;

  function reset(){
    address = '';
    privateKey = '';
    mnemonic = '';
    balance = null;
    error = '';
  }

  function createNewWallet(){
    try{
      const w = Wallet.createRandom();
      privateKey = w.privateKey;
      address = w.address;
      mnemonic = w.mnemonic?.phrase || '';
      fetchBalance();
    } catch(e){ error = e.message }
  }

  function importPrivateKey(){
    try{
      const key = importKeyInput.trim();
      if(!key) { error = 'Private key empty'; return; }
      const w = new Wallet(key);
      privateKey = w.privateKey;
      address = w.address;
      mnemonic = w.mnemonic?.phrase || '';
      fetchBalance();
    } catch(e){ error = e.message }
  }

  function importMnemonic(){
    try{
      const m = importMnemonicInput.trim();
      if(!m) { error = 'Mnemonic empty'; return; }
      const w = Wallet.fromPhrase(m);
      mnemonic = m;
      privateKey = w.privateKey;
      address = w.address;
      fetchBalance();
    } catch(e){ error = e.message }
  }

  async function fetchBalance(){
    error = '';
    balance = null;
    if(!address) return;
    try{
      provider = getDefaultProvider(network);
      const b = await provider.getBalance(address);
      balance = Number(b) / 1e18;
      // If ETH price available, compute USD equivalent
      if(prices?.ethereum?.usd) {
        balanceUSD = (balance * prices.ethereum.usd).toFixed(2);
      } else {
        balanceUSD = null;
      }
    } catch(e){ error = 'Could not fetch balance: ' + e.message }
  }

  async function fetchPrices(){
    try{
      // CoinGecko simple price endpoint (no API key required)
      const res = await fetch('https://api.coingecko.com/api/v3/simple/price?ids=ethereum,bitcoin,usd-coin&vs_currencies=usd');
      if(!res.ok) throw new Error('Price fetch failed');
      const data = await res.json();
      prices = data;
      pricesLast = new Date().toLocaleTimeString();
      // update balanceUSD if we have an ETH balance
      if(balance !== null && prices?.ethereum?.usd){
        balanceUSD = (balance * prices.ethereum.usd).toFixed(2);
      }
    } catch(e){
      // don't block UI on price fetch errors
      console.warn('Price fetch error', e);
    }
  }

  onMount(()=>{
    provider = getDefaultProvider(network);
    fetchPrices();
    // refresh prices every 30 seconds
    const tid = setInterval(fetchPrices, 30000);
    return ()=> clearInterval(tid);
  });
</script>

<div class="container">
  <div class="card">
    <h2>Svelte Crypto Wallet</h2>
    <p class="muted">Jednoduchá demo peněženka pro generování/import adres (nepoužívejte v produkci bez auditu).</p>

    <div class="field row">
      <button on:click={createNewWallet}>Nová peněženka</button>
      <button on:click={reset}>Vyčistit</button>
      <div style="margin-left:auto">
        <label class="muted">Síť:</label>
        <select bind:value={network} on:change={fetchBalance}>
          <option value="homestead">Mainnet</option>
          <option value="goerli">Goerli</option>
          <option value="sepolia">Sepolia</option>
        </select>
      </div>
    </div>

    <div class="field card">
      <label class="muted">Import private key</label>
      <div class="row" style="margin-top:8px">
        <input bind:value={importKeyInput} placeholder="0x... nebo bez 0x" style="flex:1" />
        <button on:click={importPrivateKey}>Import</button>
      </div>
    </div>

    <div class="field card" style="margin-top:12px">
      <label class="muted">Import mnemonic (seed phrase)</label>
      <div class="row" style="margin-top:8px">
        <input bind:value={importMnemonicInput} placeholder="slovo1 slovo2 ..." style="flex:1" />
        <button on:click={importMnemonic}>Import</button>
      </div>
    </div>

    {#if address}
      <div class="field" style="margin-top:12px">
        <div class="muted">Adresa</div>
        <div class="mono">{address}</div>
      </div>
    {/if}

    {#if balance !== null}
      <div class="field">
        <div class="muted">Balance ({network})</div>
        <div class="mono">{balance} ETH {#if balanceUSD} · ≈ ${balanceUSD} USD{/if}</div>
      </div>
    {/if}

    <div class="field card" style="margin-top:12px">
      <div class="muted">Tržní ceny (zdroj: CoinGecko)</div>
      <div style="margin-top:8px">
        <div class="row" style="justify-content:space-between">
          <div class="muted">Asset</div>
          <div class="muted">Cena (USD)</div>
        </div>
        <div style="margin-top:8px">
          <div class="row" style="justify-content:space-between"><div>Ethereum (ETH)</div><div class="mono">{prices.ethereum ? `$${prices.ethereum.usd}` : '—'}</div></div>
          <div class="row" style="justify-content:space-between"><div>Bitcoin (BTC)</div><div class="mono">{prices.bitcoin ? `$${prices.bitcoin.usd}` : '—'}</div></div>
          <div class="row" style="justify-content:space-between"><div>USD Coin (USDC)</div><div class="mono">{prices['usd-coin'] ? `$${prices['usd-coin'].usd}` : '—'}</div></div>
        </div>
        <div class="muted" style="margin-top:8px;font-size:12px">Aktualizováno: {pricesLast || '—'}</div>
      </div>
    </div>

    <div class="field" style="margin-top:8px">
      <label><input type="checkbox" bind:checked={showPrivate} /> Ukázat privátní klíč / mnemonic</label>
    </div>

    {#if showPrivate}
      <div class="field">
        <div class="muted">Private Key</div>
        <div class="mono">{privateKey || '—'}</div>
      </div>
      <div class="field">
        <div class="muted">Mnemonic / Seed</div>
        <div class="mono">{mnemonic || '—'}</div>
      </div>
    {/if}

    {#if error}
      <div class="field" style="color:#ffb4b4">Chyba: {error}</div>
    {/if}

    <p class="muted" style="margin-top:12px">Upozornění: Tento demo projekt zobrazuje privátní klíče v UI — nikdy nesdílejte své klíče a nepoužívejte tuto ukázku s reálnými prostředky bez auditů.</p>
  </div>
</div>
