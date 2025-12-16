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
    fetchPrices();
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
    <!-- Topbar with menu and user area -->
    <div class="topbar">
      <button class="menu-btn" on:click={() => showSidebar = true} aria-label="Open menu">☰</button>
      <div class="topbar-title">Svelte Crypto Wallet</div>
      <div class="user-area">
        <div class="avatar">{currentUser ? currentUser[0].toUpperCase() : '?'}</div>
        <button class="link" on:click={logout}>Odhlásit</button>
      </div>
    </div>

    <div class="card">
    

    <div class="field card">
      <label class="muted">Import private key</label>
      <div class="row" style="margin-top:8px">
        <input bind:value={importKeyInput} placeholder="0x... nebo bez 0x" style="flex:1" />
        <button on:click={importPrivateKey}>Import</button>
      </div>
    </div>

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
          <li><button on:click={() => { showSidebar = false; }}>Přehled zůstatků</button></li>
          <li><button on:click={() => { showSidebar = false; }}>Transakce (ukázka)</button></li>
          <li><button on:click={() => { showSidebar = false; }}>Nastavení</button></li>
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
  {/if}
</div>
