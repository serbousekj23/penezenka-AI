<script>
  import { onMount } from 'svelte';
  import { Wallet, getDefaultProvider } from 'ethers';

  let address = '';
  let privateKey = '';
  let mnemonic = '';
  let balance = null;
  let network = 'homestead';
  let error = '';
  let provider = null;

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
    } catch(e){ error = 'Could not fetch balance: ' + e.message }
  }

  onMount(()=>{
    provider = getDefaultProvider(network);
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
        <div class="mono">{balance} ETH</div>
      </div>
    {/if}

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
