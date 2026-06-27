<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	const API = 'http://localhost:8000';

	const PRODUCE_EMOJI: Record<string, string> = {
		'Apple': '🍎', 'Banana': '🍌', 'Bell Pepper': '🫑', 'Bitter Gourd': '🥬',
		'Capsicum': '🌶️', 'Carrot': '🥕', 'Cucumber': '🥒', 'Mango': '🥭',
		'Okra': '🫛', 'Orange': '🍊', 'Potato': '🥔', 'Strawberry': '🍓', 'Tomato': '🍅'
	};

	const SUPPORTED = Object.keys(PRODUCE_EMOJI).join(', ');

	type Message = { role: 'farmer' | 'barbale'; text: string };
	type ScanResult = { produce: string; freshness: string; confidence: number; advice_ka: string | null };

	let session = $state<any>(null);
	let sessionId = $state<number | null>(null);

	let messages = $state<Message[]>([]);
	let chatInput = $state('');
	let chatLoading = $state(false);
	let chatEl = $state<HTMLDivElement | null>(null);

	let imageUrl = $state<string | null>(null);
	let scanResult = $state<ScanResult | null>(null);
	let scanLoading = $state(false);

	onMount(async () => {
		const raw = localStorage.getItem('farmer_session');
		if (!raw) { goto('/'); return; }
		const parsed = JSON.parse(raw);
		if (!parsed.is_authenticated) { goto('/'); return; }
		session = parsed;

		const res = await fetch(`${API}/api/sessions`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ user_id: session.user_id })
		});
		const data = await res.json();
		sessionId = data.session_id;
	});

	$effect(() => {
		messages;
		if (chatEl) chatEl.scrollTop = chatEl.scrollHeight;
	});

	function logout() {
		localStorage.removeItem('farmer_session');
		goto('/');
	}

	async function sendMessage() {
		if (!chatInput.trim() || chatLoading || !sessionId) return;
		const msg = chatInput.trim();
		chatInput = '';
		messages = [...messages, { role: 'farmer', text: msg }];
		chatLoading = true;
		try {
			const res = await fetch(`${API}/api/chat`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ user_id: session.user_id, session_id: sessionId, message_ka: msg })
			});
			const data = await res.json();
			messages = [...messages, { role: 'barbale', text: data.response_ka }];
		} catch {
			messages = [...messages, { role: 'barbale', text: 'რაღაც შეცდომაა... სცადეთ თავიდან.' }];
		} finally {
			chatLoading = false;
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			sendMessage();
		}
	}

	async function handleImageUpload(e: Event) {
		const input = e.target as HTMLInputElement;
		if (!input.files?.[0]) return;
		const file = input.files[0];
		imageUrl = URL.createObjectURL(file);
		scanResult = null;
		scanLoading = true;
		try {
			const form = new FormData();
			form.append('file', file);
			const res = await fetch(`${API}/api/scan?user_id=${session.user_id}`, {
				method: 'POST',
				body: form
			});
			scanResult = await res.json();
		} catch {
			console.error('Scan failed');
		} finally {
			scanLoading = false;
		}
	}
</script>

<div class="workspace">
	<header>
		<div class="header-left">
			<img src="/fAIrmer.png" alt="fAIrmer" class="logo" />
			<span class="brand">fAIrmer Workspace</span>
		</div>
		<div class="header-right">
			{#if session}
				<span>👤 Farmer: {session.username}{session.region ? ` | Region: ${session.region}` : ''}</span>
			{/if}
			<button class="logout" onclick={logout}>Log out</button>
		</div>
	</header>

	<main>
		<section class="chat-panel">
			<div class="chat-scroll" bind:this={chatEl}>
				{#if messages.length === 0}
					<p class="placeholder">ბარბალეს შეუძლია გიპასუხოთ ნებისმიერ შეკითხვაზე აგრონომიასთან დაკავშირებით.</p>
				{/if}
				{#each messages as msg}
					<div class="message {msg.role}">
						<p>{msg.text}</p>
					</div>
				{/each}
				{#if chatLoading}
					<div class="message barbale">
						<p class="thinking">ბარბალე ფიქრობს...</p>
					</div>
				{/if}
			</div>

			<div class="input-bar">
				<textarea
					placeholder="დაუსვით ბარბალეს შეკითხვა..."
					bind:value={chatInput}
					onkeydown={handleKeydown}
					rows="2"
					disabled={chatLoading}
				></textarea>
				<button class="send-btn" onclick={sendMessage} disabled={chatLoading || !chatInput.trim()}>
					➤
				</button>
			</div>
		</section>

		<section class="scan-panel">
			<label class="dropzone" class:has-image={!!imageUrl}>
				{#if imageUrl}
					<img src={imageUrl} alt="Uploaded crop" class="preview" />
				{:else}
					<div class="dropzone-inner">
						<span class="upload-icon">📁</span>
						<p>Upload a crop image</p>
						<p class="supported">Supported: {SUPPORTED}</p>
					</div>
				{/if}
				<input type="file" accept="image/*" onchange={handleImageUpload} />
			</label>

			{#if scanLoading}
				<div class="metrics">
					<p class="scanning">ბარბალე უყურებს ფოტოს...</p>
				</div>
			{/if}

			{#if scanResult}
				<div class="metrics">
					<div class="metric-row">
						<span class="metric-label">Produce Type</span>
						<span class="metric-value">{PRODUCE_EMOJI[scanResult.produce] ?? '🌿'} {scanResult.produce}</span>
					</div>
					<div class="metric-row">
						<span class="metric-label">Freshness</span>
						<span class="badge" class:fresh={scanResult.freshness === 'Fresh'} class:rotten={scanResult.freshness === 'Rotten'}>
							{scanResult.freshness} ({(scanResult.confidence * 100).toFixed(1)}%)
						</span>
					</div>
				</div>

				{#if scanResult.freshness === 'Rotten' && scanResult.advice_ka}
					<div class="advisory">
						<p class="advisory-title">⚠️ კრიტიკული მდგომარეობა (Critical Situation Mitigation Advice)</p>
						<p class="advisory-text">{scanResult.advice_ka}</p>
					</div>
				{/if}
			{/if}
		</section>
	</main>
</div>

<style>
	.workspace {
		display: flex;
		flex-direction: column;
		height: 100vh;
		overflow: hidden;
	}

	header {
		background: var(--green);
		color: white;
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.75rem 1.5rem;
		flex-shrink: 0;
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}

	.logo {
		width: 36px;
		height: 36px;
		object-fit: contain;
	}

	.brand {
		font-size: 1.1rem;
		font-weight: 600;
	}

	.header-right {
		display: flex;
		align-items: center;
		gap: 1rem;
		font-size: 0.9rem;
	}

	.logout {
		background: transparent;
		border: 1.5px solid rgba(255,255,255,0.6);
		color: white;
		padding: 0.3rem 0.8rem;
		border-radius: 6px;
		cursor: pointer;
		font-size: 0.85rem;
		transition: background 0.15s;
	}

	.logout:hover {
		background: rgba(255,255,255,0.15);
	}

	main {
		display: grid;
		grid-template-columns: 1fr 1fr;
		flex: 1;
		overflow: hidden;
		gap: 0;
	}

	/* ── Chat ── */
	.chat-panel {
		display: flex;
		flex-direction: column;
		border-right: 1.5px solid #e0e0e0;
		overflow: hidden;
	}

	.chat-scroll {
		flex: 1;
		overflow-y: auto;
		padding: 1.25rem;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.placeholder {
		color: #999;
		font-size: 0.9rem;
		text-align: center;
		margin-top: 2rem;
	}

	.message {
		max-width: 80%;
		padding: 0.65rem 1rem;
		border-radius: 10px;
		font-size: 0.95rem;
		line-height: 1.5;
		word-break: break-word;
	}

	.message.farmer {
		align-self: flex-end;
		background: var(--sage);
		color: var(--dark);
	}

	.message.barbale {
		align-self: flex-start;
		background: white;
		border-left: 4px solid var(--green);
		box-shadow: 0 1px 4px rgba(0,0,0,0.06);
	}

	.thinking {
		color: #888;
		font-style: italic;
	}

	.input-bar {
		display: flex;
		align-items: flex-end;
		gap: 0.5rem;
		padding: 0.75rem 1rem;
		border-top: 1.5px solid #e0e0e0;
		background: white;
	}

	.input-bar textarea {
		flex: 1;
		resize: none;
		border: 1.5px solid #ddd;
		border-radius: 10px;
		padding: 0.6rem 0.85rem;
		font-size: 0.95rem;
		font-family: inherit;
		outline: none;
		transition: border-color 0.15s;
	}

	.input-bar textarea:focus {
		border-color: var(--sage);
	}

	.send-btn {
		width: 44px;
		height: 44px;
		border-radius: 50%;
		background: var(--green);
		color: white;
		border: none;
		font-size: 1.1rem;
		cursor: pointer;
		flex-shrink: 0;
		transition: background 0.15s;
	}

	.send-btn:hover:not(:disabled) {
		background: var(--sage);
	}

	.send-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	/* ── Scanner ── */
	.scan-panel {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		padding: 1.25rem;
		overflow-y: auto;
		background: white;
	}

	.dropzone {
		display: block;
		border: 2px dashed var(--sage);
		border-radius: 12px;
		min-height: 200px;
		cursor: pointer;
		transition: border-color 0.15s;
		overflow: hidden;
		position: relative;
	}

	.dropzone:hover {
		border-color: var(--green);
	}

	.dropzone input[type="file"] {
		display: none;
	}

	.dropzone-inner {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		padding: 2rem;
		text-align: center;
		color: #888;
	}

	.upload-icon {
		font-size: 2.5rem;
	}

	.supported {
		font-size: 0.78rem;
		line-height: 1.4;
	}

	.preview {
		width: 100%;
		height: 200px;
		object-fit: cover;
		display: block;
	}

	.metrics {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.scanning {
		color: #888;
		font-style: italic;
		font-size: 0.9rem;
	}

	.metric-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.5rem 0.75rem;
		background: var(--cream);
		border-radius: 8px;
		font-size: 0.95rem;
	}

	.metric-label {
		color: #666;
		font-size: 0.85rem;
	}

	.metric-value {
		font-weight: 600;
	}

	.badge {
		padding: 0.3rem 0.75rem;
		border-radius: 20px;
		font-weight: 600;
		font-size: 0.9rem;
	}

	.badge.fresh {
		background: #d4edda;
		color: #155724;
	}

	.badge.rotten {
		background: var(--gold);
		color: var(--dark);
	}

	.advisory {
		border: 2px solid var(--gold);
		border-radius: 10px;
		padding: 1rem;
		background: #fffde7;
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}

	.advisory-title {
		font-weight: 700;
		font-size: 0.95rem;
		color: var(--dark);
	}

	.advisory-text {
		font-size: 0.9rem;
		line-height: 1.6;
		color: #444;
	}
</style>
