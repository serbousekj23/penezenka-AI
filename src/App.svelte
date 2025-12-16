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

  // Simple auth
  const AUTH_KEY = 'wallet_auth';
  let isAuthenticated = false;
  let authMode = 'login'; // 'login' | 'register'
  let loginUsername = '';
  let loginPassword = '';
  let regUsername = '';
  let regPassword = '';
  let regConfirm = '';
  let currentUser = '';
  let showSidebar = false;
  let showConfirmReset = false;
  let currentView = 'welcome'; // 'welcome' | 'wallet' | 'prices'

  // Portfolio / virtual cash / transactions (local, fake)
  const PORTFOLIO_KEY = 'wallet_portfolio';
  const TX_KEY = 'wallet_txs';
  const CASH_KEY = 'wallet_cash';
  const CURRENCY_KEY = 'wallet_currency';
  let portfolio = { ethereum: 0, bitcoin: 0, 'usd-coin': 0 };
  let txs = [];
  // virtualCash is stored in the currently selected base currency
  let virtualCash = 1000; // default will be set on registration/load
  let baseCurrency = 'USD';
  let fiatRates = { USD: 1 }; // USD -> other fiat rates
  let showBuyModal = false;
  let showSettings = false;
  let buyAssetSelect = 'ethereum';
  let buyQty = '';
  let sellAsset = '';
  let sellAmount = '';
  let showSellModal = false;
  let settingsCash = '';

  // Prices fetched from CoinGecko
  let prices = {};
  let pricesLast = null;
  let histPrices = [];
  let chartAsset = 'ethereum';
  let chartRange = 7;

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

  // Local portfolio helpers
  function loadState(){
    try{
      const p = localStorage.getItem(PORTFOLIO_KEY);
      if(p) portfolio = JSON.parse(p);
      const t = localStorage.getItem(TX_KEY);
      if(t) txs = JSON.parse(t);
      const c = localStorage.getItem(CASH_KEY);
      const savedCurrency = localStorage.getItem(CURRENCY_KEY) || 'USD';
      baseCurrency = savedCurrency;
      if(c) virtualCash = Number(c);
    } catch(e){ console.warn('Load state error', e); }
  }

  function saveState(){
    try{
      localStorage.setItem(PORTFOLIO_KEY, JSON.stringify(portfolio));
      localStorage.setItem(TX_KEY, JSON.stringify(txs));
      localStorage.setItem(CASH_KEY, String(virtualCash));
      localStorage.setItem(CURRENCY_KEY, baseCurrency);
    } catch(e){ console.warn('Save state error', e); }
  }

  function addTx(tx){ txs = [tx, ...txs]; saveState(); }

  function openBuy(){ buyQty = ''; buyAssetSelect = 'ethereum'; showBuyModal = true; }

  function closeBuy(){ showBuyModal = false; }

  function openSettings(){ settingsCash = String(virtualCash); showSettings = true; }
  function closeSettings(){ showSettings = false; }

  function doBuy(){
    error = '';
    const qty = Number(buyQty);
    if(!qty || qty <= 0){ error = 'Zadejte množství aktiva větší než 0'; return; }
    const priceUSD = prices?.[buyAssetSelect]?.usd;
    if(!priceUSD){ error = 'Cena není načtena'; return; }
    // compute price and cost in base currency
    const rate = fiatRates[baseCurrency] || 1;
    const priceInBase = Number((priceUSD * rate).toFixed(6));
    const costInBase = Number((qty * priceInBase).toFixed(2));
    if(costInBase > virtualCash){ error = 'Nedostatek virtuálních prostředků'; return; }
    portfolio[buyAssetSelect] = (portfolio[buyAssetSelect] || 0) + qty;
    virtualCash = Number((virtualCash - costInBase).toFixed(2));
    const tx = { type:'buy', asset: buyAssetSelect, qty, usd: Number((qty*priceUSD).toFixed(2)), priceUSD, priceInBase, costInBase, currency: baseCurrency, time: Date.now() };
    addTx(tx);
    saveState();
    showBuyModal = false;
    buyQty = '';
  }

  function doSell(){
    error = '';
    let amt = Number(sellAmount);
    if(!sellAsset){ error = 'Vyberte aktivum'; return; }
    if(!amt || amt <= 0){ error = 'Zadejte množství k prodeji'; return; }
    if((portfolio[sellAsset] || 0) < amt){ error = 'Nedostatečný počet měny'; return; }
    const priceUSD = prices?.[sellAsset]?.usd;
    if(!priceUSD){ error = 'Cena není načtena'; return; }
    const rate = fiatRates[baseCurrency] || 1;
    const priceInBase = Number((priceUSD * rate).toFixed(6));
    const usd = Number((amt * priceUSD).toFixed(2));
    const proceedsInBase = Number((amt * priceInBase).toFixed(2));
    portfolio[sellAsset] = Math.max(0, (portfolio[sellAsset] || 0) - amt);
    virtualCash = Number((virtualCash + proceedsInBase).toFixed(2));
    const tx = { type:'sell', asset: sellAsset, qty: amt, usd, priceUSD, priceInBase, proceedsInBase, currency: baseCurrency, time: Date.now() };
    addTx(tx);
    saveState();
    sellAmount = '';
    sellAsset = '';
  }

  // Fetch fiat exchange rates (USD base)
  async function fetchFiatRates(){
    try{
      const res = await fetch('https://api.exchangerate.host/latest?base=USD&symbols=USD,EUR,CZK');
      if(!res.ok) throw new Error('Fiat rates fetch failed');
      const data = await res.json();
      fiatRates = data.rates || { USD:1 };
    } catch(e){ console.warn('Fiat rates error', e); fiatRates = { USD:1 }; }
  }

  function formatCurrency(amount){
    const sym = baseCurrency === 'USD' ? '$' : baseCurrency === 'EUR' ? '€' : 'Kč';
    if(amount == null) return `- ${baseCurrency}`;
    return `${sym}${Number(amount).toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}`;
  }

  // Charts: fetch historical market data from CoinGecko (prices in USD) and store
  async function fetchChartData(asset, days){
    histPrices = [];
    try{
      const res = await fetch(`https://api.coingecko.com/api/v3/coins/${asset}/market_chart?vs_currency=usd&days=${days}`);
      if(!res.ok) throw new Error('Chart fetch failed');
      const data = await res.json();
      // data.prices is [[ts, price], ...]
      // convert to numbers (price in base currency if needed)
      const rate = fiatRates[baseCurrency] || 1;
      histPrices = (data.prices || []).map(p => ({ t: p[0], v: Number((p[1] * rate).toFixed(6)) }));
    } catch(e){ console.warn('Chart error', e); histPrices = []; }
  }

  function svgPoints(w=640,h=200){
    if(!histPrices || histPrices.length === 0) return '';
    const n = histPrices.length;
    const vals = histPrices.map(x => x.v);
    const min = Math.min(...vals);
    const max = Math.max(...vals);
    const pad = 6;
    return histPrices.map((pt, i) => {
      const x = pad + (i / (n - 1)) * (w - pad*2);
      const y = (h - pad) - ((pt.v - min) / (max - min || 1)) * (h - pad*2);
      return `${x},${y}`;
    }).join(' ');
  }

  function setVirtualCash(v){
    const n = Number(v);
    if(isNaN(n) || n < 0) return;
    virtualCash = n;
    saveState();
  }

  // --- Auth helpers ---
  function buf2hex(buffer){
    return Array.prototype.map.call(new Uint8Array(buffer), x => ('00' + x.toString(16)).slice(-2)).join('');
  }

  async function hashPassword(pw){
    const enc = new TextEncoder();
    const data = enc.encode(pw);
    const hashBuf = await crypto.subtle.digest('SHA-256', data);
    return buf2hex(hashBuf);
  }

  async function register(){
    error = '';
    if(!regUsername) { error = 'Uživatelské jméno je povinné'; return; }
    if(!regPassword) { error = 'Heslo nesmí být prázdné'; return; }
    if(regPassword.length < 8){ error = 'Heslo musí mít minimálně 8 znaků'; return; }
    if(regPassword !== regConfirm){ error = 'Hesla se neshodují'; return; }
    try{
      const h = await hashPassword(regPassword);
      const payload = { username: regUsername, hash: h };
      localStorage.setItem(AUTH_KEY, JSON.stringify(payload));
      isAuthenticated = true;
      currentUser = regUsername;
      currentView = 'welcome';
      // initialize virtual cash for new user (1000 in base currency)
      baseCurrency = 'USD';
      virtualCash = 1000;
      saveState();
      // clear reg inputs
      regUsername = '';
      regPassword = '';
      regConfirm = '';
    } catch(e){ error = e.message }
  }

  async function login(){
    error = '';
    const stored = localStorage.getItem(AUTH_KEY);
    if(!stored){ error = 'Žádný účet není registrován — zaregistrujte se nejdříve'; return; }
    try{
      const payload = JSON.parse(stored);
      if(!loginUsername){ error = 'Uživatelské jméno je povinné'; return; }
      if(!loginPassword || loginPassword.length < 8){ error = 'Heslo musí mít minimálně 8 znaků'; return; }
      if(payload.username !== loginUsername){ error = 'Uživatelské jméno neexistuje'; return; }
      const h = await hashPassword(loginPassword);
      if(h === payload.hash){
        isAuthenticated = true;
        currentUser = loginUsername;
        currentView = 'welcome';
        loadState();
        loginUsername = '';
        loginPassword = '';
      } else {
        error = 'Nesprávné heslo';
      }
    } catch(e){ error = e.message }
  }

  function logout(){
    isAuthenticated = false;
    reset();
    currentUser = '';
  }

  function cancelReset(){
    showConfirmReset = false;
  }

  function doReset(){
    try{
      localStorage.removeItem(AUTH_KEY);
    } catch(e){ console.warn('Reset error', e); }
    showConfirmReset = false;
    showSidebar = false;
    logout();
  }

  onMount(()=>{
    provider = getDefaultProvider(network);
    // fetch fiat rates first, then load saved state so currency conversion is available
    fetchFiatRates().then(()=>{
      loadState();
      // update UI prices after state loaded
      fetchPrices();
    });
    // refresh prices every 30 seconds
    const tid = setInterval(fetchPrices, 30000);
    return ()=> clearInterval(tid);
  });
</script>

<div class="container">
  {#if !isAuthenticated}
    <div class="card">
      <h2>Svelte Crypto Wallet — Přihlášení</h2>
      <p class="muted">Pro přístup k peněžence se musíte přihlásit nebo zaregistrovat lokálně (demo).</p>

      <div class="field card">
        <label class="muted">Přihlásit</label>
        <div class="row" style="margin-top:8px">
          <input bind:value={loginUsername} placeholder="Uživatelské jméno" style="flex:1;margin-right:8px" />
          <input type="password" bind:value={loginPassword} placeholder="Heslo" style="flex:1;margin-right:8px" />
          <button on:click={login}>Přihlásit</button>
        </div>
      </div>

      <div class="field card" style="margin-top:12px">
        <label class="muted">Registrovat nový účet</label>
        <div style="margin-top:8px">
          <input bind:value={regUsername} placeholder="Uživatelské jméno" style="width:100%;margin-bottom:8px" />
          <input type="password" bind:value={regPassword} placeholder="Nové heslo (min. 8 znaků)" style="width:100%;margin-bottom:8px" />
          <input type="password" bind:value={regConfirm} placeholder="Potvrzení hesla" style="width:100%;margin-bottom:8px" />
          <div class="row"><button on:click={register}>Registrovat</button></div>
        </div>
      </div>

      {#if error}
        <div class="field" style="color:#ffb4b4">Chyba: {error}</div>
      {/if}

    </div>
  {/if}

  {#if isAuthenticated}
    <!-- Topbar with home, menu and user area -->
    <div class="topbar">
      <div class="left-area">
        <button class="home-btn" on:click={() => { currentView = 'welcome'; }} aria-label="Home">🏠</button>
        <button class="menu-btn" on:click={() => showSidebar = true} aria-label="Open menu">☰</button>
      </div>
      <div class="topbar-title">Svelte Crypto Wallet</div>
      <div class="user-area">
        <div class="avatar">{currentUser ? currentUser[0].toUpperCase() : '?'}</div>
        <div class="cash-inline">{formatCurrency(virtualCash)}</div>
        <button class="link" on:click={logout}>Odhlásit</button>
      </div>
    </div>

    {#if currentView === 'welcome'}
      <div class="card welcome-card">
        <h2>Vítejte{#if currentUser}, {currentUser}{/if}!</h2>
        <p class="muted">Vyberte jednu z možností pro pokračování.</p>
        <div class="welcome-ctas">
          <button class="big-cta" on:click={() => currentView = 'wallet'}>Otevřít peněženku</button>
          <button class="big-cta ghost" on:click={() => currentView = 'prices'}>Souhrn cen</button>
        </div>
      </div>
    {/if}

    {#if currentView === 'charts'}
      <div class="card">
        <h2>Grafy cen</h2>
        <p class="muted">Vyberte aktivum a časové rozmezí</p>
        <div style="margin-top:8px;display:flex;gap:8px;align-items:center">
          <select bind:value={chartAsset} style="padding:8px;border-radius:8px">
            <option value="ethereum">Ethereum (ETH)</option>
            <option value="bitcoin">Bitcoin (BTC)</option>
            <option value="usd-coin">USD Coin (USDC)</option>
          </select>
          <select bind:value={chartRange} style="padding:8px;border-radius:8px">
            <option value="1">1 den</option>
            <option value="7">7 dní</option>
            <option value="30">30 dní</option>
            <option value="90">90 dní</option>
            <option value="365">365 dní</option>
          </select>
          <button on:click={() => fetchChartData(chartAsset, chartRange)}>Načíst graf</button>
          <div style="margin-left:auto" class="muted">Aktuální (poslední): {histPrices.length ? formatCurrency(histPrices[histPrices.length-1].v) : '—'}</div>
        </div>
        <div style="margin-top:12px">
          {#if histPrices.length === 0}
            <div class="muted">Graf není načten. Klikněte 'Načíst graf'.</div>
          {:else}
            <div class="chart-container">
              <svg viewBox="0 0 640 220" preserveAspectRatio="none" width="100%" height="220">
                <polyline fill="none" stroke="#60a5fa" stroke-width="2" points="{svgPoints(640,200)}" />
              </svg>
              <div class="muted" style="font-size:12px;margin-top:6px">Rozsah: {chartRange} dní · Měna: {baseCurrency}</div>
            </div>
          {/if}
        </div>
        <div style="margin-top:12px" class="row"><button on:click={() => currentView = 'welcome'}>Zpět</button></div>
      </div>
    {/if}

    {#if currentView === 'transactions'}
      <div class="card">
        <h2>Transakce</h2>
        <p class="muted">Seznam nákupů a prodejů (virtuální)</p>
        <div style="margin-top:12px">
          {#if txs.length === 0}
            <div class="muted">Žádné transakce</div>
          {:else}
            <table style="width:100%;border-collapse:collapse">
              <thead>
                <tr style="text-align:left;border-bottom:1px solid rgba(255,255,255,0.04)"><th>Typ</th><th>Asset</th><th>Množství</th><th>USD</th><th>Cena</th><th>Čas</th></tr>
              </thead>
              <tbody>
                {#each txs as t}
                  <tr style="height:40px;border-bottom:1px solid rgba(255,255,255,0.02)">
                    <td>{t.type === 'buy' ? 'Nákup' : 'Prodej'}</td>
                    <td>{t.asset === 'usd-coin' ? 'USDC' : t.asset === 'ethereum' ? 'ETH' : 'BTC'}</td>
                    <td>{t.qty.toFixed(6)}</td>
                    <td>${t.usd}</td>
                    <td>${t.price}</td>
                    <td>{new Date(t.time).toLocaleString()}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          {/if}
        </div>
        <div style="margin-top:12px" class="row"><button on:click={() => currentView = 'welcome'}>Zpět</button></div>
      </div>
    {/if}

    {#if currentView === 'prices'}
      <div class="card">
        <h2>Souhrn cen</h2>
        <p class="muted">Aktuální tržní ceny (zdroj: CoinGecko)</p>
        <div style="margin-top:8px">
          <div class="row" style="justify-content:space-between"><div>Ethereum (ETH)</div><div class="mono">{prices.ethereum ? formatCurrency(prices.ethereum.usd * (fiatRates[baseCurrency]||1)) : '—'}</div></div>
          <div class="row" style="justify-content:space-between"><div>Bitcoin (BTC)</div><div class="mono">{prices.bitcoin ? formatCurrency(prices.bitcoin.usd * (fiatRates[baseCurrency]||1)) : '—'}</div></div>
          <div class="row" style="justify-content:space-between"><div>USD Coin (USDC)</div><div class="mono">{prices['usd-coin'] ? formatCurrency(prices['usd-coin'].usd * (fiatRates[baseCurrency]||1)) : '—'}</div></div>
        </div>
        <div class="muted" style="margin-top:8px;font-size:12px">Aktualizováno: {pricesLast || '—'}</div>
        <div style="margin-top:12px" class="row"><button on:click={() => currentView = 'welcome'}>Zpět</button></div>
      </div>
    {/if}

    {#if currentView === 'wallet'}
      <div class="card">
        <h2>Portfolio</h2>
        <p class="muted">Virtuální hotovost: <strong>{formatCurrency(virtualCash)}</strong></p>
        <table style="width:100%;margin-top:12px;border-collapse:collapse">
          <thead>
            <tr style="text-align:left;border-bottom:1px solid rgba(255,255,255,0.04)">
              <th>Asset</th>
              <th>Množství</th>
              <th>Cena (USD)</th>
              <th>Hodnota (USD)</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {#each Object.keys(portfolio) as a}
              <tr style="border-bottom:1px solid rgba(255,255,255,0.02);height:44px">
                <td style="text-transform:capitalize">{a === 'usd-coin' ? 'USDC' : a === 'ethereum' ? 'ETH' : 'BTC'}</td>
                <td>{(portfolio[a] || 0).toFixed(6)}</td>
                <td>{prices[a] ? formatCurrency(prices[a].usd * (fiatRates[baseCurrency] || 1)) : '—'}</td>
                <td>{prices[a] ? formatCurrency(((portfolio[a]||0) * prices[a].usd) * (fiatRates[baseCurrency] || 1)) : '—'}</td>
                <td><button class="link" on:click={() => { sellAsset = a; showSellModal = true; }}>Prodat</button></td>
              </tr>
            {/each}
          </tbody>
        </table>
        <div style="margin-top:12px" class="row">
          <button on:click={openBuy}>Koupit</button>
          <button on:click={() => currentView = 'transactions'} style="margin-left:auto">Zobrazit transakce</button>
        </div>
      </div>
    {/if}

    <!-- Sidebar + overlay -->
    {#if showSidebar}
      <div class="overlay" on:click={() => showSidebar = false}></div>
    {/if}
    <aside class="sidebar {showSidebar ? 'open' : ''}">
      <div class="sidebar-header">
        <div class="avatar small">{currentUser ? currentUser[0].toUpperCase() : '?'}</div>
        <div style="margin-left:8px">{currentUser}</div>
      </div>
      <nav>
        <ul>
          <li><button on:click={() => { showSidebar = false; currentView = 'wallet'; }}>Přehled zůstatků</button></li>
          <li><button on:click={() => { showSidebar = false; currentView = 'transactions'; }}>Transakce</button></li>
          <li><button on:click={() => { showSidebar = false; currentView = 'charts'; }}>Grafy</button></li>
          <li><button on:click={() => { showSidebar = false; openBuy(); }}>Zakoupit</button></li>
          <li><button on:click={() => { showSidebar = false; openSettings(); }}>Nastavení</button></li>
          <li><button on:click={() => { showConfirmReset = true; }}>Reset účtu</button></li>
        </ul>
      </nav>
    </aside>

    {#if showConfirmReset}
      <div class="modal-overlay" on:click={cancelReset}></div>
      <div class="modal" role="dialog" aria-modal="true">
        <div class="modal-content">
          <h3>Opravdu smazat účet?</h3>
          <p>Tato akce smaže lokálně uložené přihlašovací údaje a odhlásí vás. Pokračovat?</p>
          <div class="modal-actions">
            <button on:click={doReset}>Ano, smazat</button>
            <button class="link" on:click={cancelReset}>Zrušit</button>
          </div>
        </div>
      </div>
    {/if}

    {#if showBuyModal}
      <div class="modal-overlay" on:click={closeBuy}></div>
      <div class="modal" role="dialog" aria-modal="true">
        <div class="modal-content">
          <h3>Nákup (virtuální)</h3>
          <div style="margin-top:8px">
            <label class="muted">Asset</label>
            <select bind:value={buyAssetSelect} style="width:100%;margin-top:6px">
              <option value="ethereum">Ethereum (ETH)</option>
              <option value="bitcoin">Bitcoin (BTC)</option>
              <option value="usd-coin">USD Coin (USDC)</option>
            </select>
            <label class="muted" style="margin-top:8px">Množství aktiva k nákupu</label>
            <input bind:value={buyQty} placeholder="např. 0.01" style="width:100%;margin-top:6px" />
            <div class="muted" style="margin-top:8px">{#if prices[buyAssetSelect]}Přibližná cena: {(buyQty && !isNaN(Number(buyQty)) ? formatCurrency(Number(buyQty)*prices[buyAssetSelect].usd*(fiatRates[baseCurrency]||1)) : '—')}{/if}</div>
          </div>
          <div class="modal-actions">
            <button on:click={doBuy}>Koupit</button>
            <button class="link" on:click={closeBuy}>Zrušit</button>
          </div>
        </div>
      </div>
    {/if}

    {#if showSellModal}
      <div class="modal-overlay" on:click={() => { showSellModal = false; sellAmount = ''; sellAsset=''; }}></div>
      <div class="modal" role="dialog" aria-modal="true">
        <div class="modal-content">
          <h3>Prodej {sellAsset === 'usd-coin' ? 'USDC' : sellAsset === 'ethereum' ? 'ETH' : 'BTC'}</h3>
          <div style="margin-top:8px">
            <label class="muted">Množství</label>
              <input bind:value={sellAmount} placeholder="Množství k prodeji" style="width:100%;margin-top:6px" />
              <div class="row" style="margin-top:8px;gap:8px">
                <button on:click={() => { sellAmount = (portfolio[sellAsset] || 0).toString(); }}>Prodat vše</button>
                <div class="muted">{#if prices[sellAsset]}Přibližně {(sellAmount && !isNaN(Number(sellAmount)) ? formatCurrency(Number(sellAmount)*prices[sellAsset].usd*(fiatRates[baseCurrency]||1)) : '—')}{/if}</div>
              </div>
          </div>
          <div class="modal-actions">
            <button on:click={() => { doSell(); showSellModal = false; }}>Prodat</button>
            <button class="link" on:click={() => { showSellModal = false; sellAmount=''; sellAsset=''; }}>Zrušit</button>
          </div>
        </div>
      </div>
    {/if}

    {#if showSettings}
      <div class="modal-overlay" on:click={closeSettings}></div>
      <div class="modal" role="dialog" aria-modal="true">
        <div class="modal-content">
          <h3>Nastavení</h3>
          <div style="margin-top:8px">
            <label class="muted">Použitá měna</label>
            <select bind:value={baseCurrency} style="width:100%;margin-top:6px">
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
              <option value="CZK">CZK</option>
            </select>
            <div class="muted" style="margin-top:8px">Aktuální zůstatek: {formatCurrency(virtualCash)}</div>
          </div>
          <div class="modal-actions">
            <button on:click={() => {
              // convert virtualCash to newly selected baseCurrency using fiatRates
              const old = localStorage.getItem(CURRENCY_KEY) || 'USD';
              const oldRate = fiatRates[old] || 1;
              const newRate = fiatRates[baseCurrency] || 1;
              // if rates available, adjust stored cash amount so the USD-equivalent remains
              // compute USD equivalent of current cash: usdEquivalent = virtualCash / oldRate
              // then new cash = usdEquivalent * newRate
              try{
                const usdEquivalent = (virtualCash / oldRate) || 0;
                virtualCash = Number((usdEquivalent * newRate).toFixed(2));
              } catch(e){ console.warn('Conversion error', e); }
              saveState();
              closeSettings();
            }}>Uložit</button>
            <button class="link" on:click={closeSettings}>Zrušit</button>
          </div>
        </div>
      </div>
    {/if}
  {/if}
</div>
