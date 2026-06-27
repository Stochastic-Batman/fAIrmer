<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	const API = 'http://localhost:8000';

	const PRODUCE_EMOJI: Record<string, string> = {
	    'Apple': '🍎', 'Banana': '🍌', 'Bell Pepper': '🫑', 'Bitter Gourd': '🥬',
	    'Capsicum': '🌶️', 'Carrot': '🥕', 'Cucumber': '🥒', 'Mango': '🥭',
	    'Okra': '🫛', 'Orange': '🍊', 'Potato': '🥔', 'Strawberry': '🍓', 'Tomato': '🍅'
	};
	
	const PRODUCTS_TO_GEORGIAN: Record<string, string> = {
	    'Apple': 'ვაშლი', 'Banana': 'ბანანი', 'Bell Pepper': 'ბულგარული წიწაკა', 'bitter gourd': 'მწარე ნესვი',
	    'Capsicum': 'წიწაკა', 'Carrot': 'სტაფილო', 'Cucumber': 'კიტრი', 'Mango': 'მანგო',
	    'Okra': 'ბამი', 'Orange': 'ფორთოხალი', 'Potato': 'კარტოფილი', 'Strawberry': 'მარწყვი', 'Tomato': 'პომიდორი'
	};

	const REGION_EN_TO_KA: Record<string, string> = {
	    'Kakheti': 'კახეთი', 'Imereti': 'იმერეთი', 'Samegrelo': 'სამეგრელო',
	    'Kartli': 'ქართლი', 'Adjara': 'აჭარა', 'Guria': 'გურია',
	    'Racha': 'რაჭა', 'Svaneti': 'სვანეთი', 'Mtskheta-Mtianeti': 'მცხეთა-მთიანეთი',
	    'Kvemo Kartli': 'ქვემო ქართლი', 'Shida Kartli': 'შიდა ქართლი',
	    'Samtskhe-Javakheti': 'სამცხე-ჯავახეთი', 'Abkhazia': 'აფხაზეთი',
	};

	function localizeRegion(r: string): string {
		return REGION_EN_TO_KA[r] ?? r;
	}

	function localizeCrops(crops: string): string {
		return crops.split(',').map(c => PRODUCTS_TO_GEORGIAN[c.trim()] ?? c.trim()).join(', ');
	}

	const SUPPORTED = Object.values(PRODUCTS_TO_GEORGIAN).join(', ');

	type Message = { role: 'farmer' | 'barbale'; text: string };
	type ScanResult = { produce: string; freshness: string; confidence: number; advice_ka: string | null };
	type AlertLog = { alert_id: number; produce: string; freshness: string; confidence: number; advice_ka: string; created_at: string };

	let session = $state<any>(null);
	let sessionId = $state<number | null>(null);

	let messages = $state<Message[]>([]);
	let chatInput = $state('');
	let chatLoading = $state(false);
	let chatEl = $state<HTMLDivElement | null>(null);

	let imageUrl = $state<string | null>(null);
	let scanResult = $state<ScanResult | null>(null);
	let scanLoading = $state(false);
	let alerts = $state<AlertLog[]>([]);

	async function fetchAlerts(userId: number) {
		try {
			const res = await fetch(`${API}/api/alerts/${userId}`);
			alerts = await res.json();
		} catch { /* non-critical */ }
	}

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

		fetchAlerts(session.user_id);
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
			fetchAlerts(session.user_id);
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
			<span class="brand">fAIrmer</span>
		</div>
		<div class="header-right">
			{#if session}
				<span>👤 {session.username}</span>
			{/if}
			<button class="logout" onclick={logout}>გასვლა</button>
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

			{#if scanResult || scanLoading}
				<div class="mobile-scan-strip">
					{#if scanLoading}
						<p class="scanning">ბარბალე უყურებს ფოტოს...</p>
					{:else if scanResult}
						<div class="strip-row">
							<span>{PRODUCE_EMOJI[scanResult.produce] ?? '🌿'} {scanResult.produce}</span>
							<span class="badge" class:fresh={scanResult.freshness === 'Fresh'} class:rotten={scanResult.freshness === 'Rotten'}>
								{scanResult.freshness} ({(scanResult.confidence * 100).toFixed(1)}%)
							</span>
						</div>
						{#if scanResult.freshness === 'Rotten' && scanResult.advice_ka}
							<p class="strip-advisory">⚠️ {scanResult.advice_ka}</p>
						{/if}
					{/if}
				</div>
			{/if}

			<div class="input-bar">
				<label class="upload-btn" title="ფოტოს ატვირთვა">
					📎
					<input type="file" accept="image/*" onchange={handleImageUpload} />
				</label>
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
			{#if session}
				<div class="profile-card">
					<p class="profile-name">👤 {session.username}</p>
					<div class="profile-meta">
						{#if session.region}<span class="profile-tag">📍 {localizeRegion(session.region)}</span>{/if}
						{#if session.primary_crops}<span class="profile-tag">🌾 {localizeCrops(session.primary_crops)}</span>{/if}
						{#if session.soil_metrics}<span class="profile-tag">🪨 {session.soil_metrics}</span>{/if}
					</div>
				</div>
			{/if}

			<label class="dropzone" class:has-image={!!imageUrl}>
				{#if imageUrl}
					<img src={imageUrl} alt="Uploaded crop" class="preview" />
				{:else}
					<div class="dropzone-inner">
						<span class="upload-icon">📁</span>
						<p>ატვირთეთ მოსავლის ფოტო</p>
						<p class="supported">ამჟამად მხარდაჭერილია: {SUPPORTED}</p>
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
						<span class="metric-label">კულტურა</span>
						<span class="metric-value">{PRODUCE_EMOJI[scanResult.produce] ?? '🌿'} {PRODUCTS_TO_GEORGIAN[scanResult.produce] ?? scanResult.produce}</span>
					</div>
					<div class="metric-row">
						<span class="metric-label">სიახლე</span>
						<span class="badge" class:fresh={scanResult.freshness === 'Fresh'} class:rotten={scanResult.freshness === 'Rotten'}>
							{scanResult.freshness === 'Fresh' ? 'ახალი' : 'გაფუჭებული'} ({(scanResult.confidence * 100).toFixed(1)}%)
						</span>
					</div>
				</div>

				{#if scanResult.freshness === 'Rotten' && scanResult.advice_ka}
					<div class="advisory">
						<p class="advisory-title">⚠️ კრიტიკული მდგომარეობა</p>
						<p class="advisory-text">{scanResult.advice_ka}</p>
					</div>
				{/if}
			{/if}

			{#if alerts.length > 0}
				<div class="alert-history">
					<p class="alert-history-title">გაფრთხილებების ისტორია</p>
					{#each alerts.slice(0, 5) as alert}
						<div class="alert-item">
							<div class="alert-item-header">
								<span>{PRODUCE_EMOJI[alert.produce] ?? '🌿'} {PRODUCTS_TO_GEORGIAN[alert.produce] ?? alert.produce}</span>
								<span class="alert-date">{alert.created_at.slice(0, 10)}</span>
							</div>
							{#if alert.advice_ka}
								<p class="alert-advice">{alert.advice_ka}</p>
							{/if}
						</div>
					{/each}
				</div>
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

	/* Chat */
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

	/* Scanner */
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

	/* Profile card */
	.profile-card {
		background: var(--cream);
		border-radius: 10px;
		padding: 0.75rem 1rem;
		display: flex;
		flex-direction: column;
		gap: 0.4rem;
	}
	.profile-name {
		font-weight: 600;
		font-size: 0.95rem;
		color: var(--dark);
	}
	.profile-meta {
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem;
	}
	.profile-tag {
		background: white;
		border: 1px solid #d0d0d0;
		border-radius: 20px;
		padding: 0.2rem 0.65rem;
		font-size: 0.8rem;
		color: #555;
	}

	/* Alert history */
	.alert-history {
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
		margin-top: 0.25rem;
	}
	.alert-history-title {
		font-size: 0.8rem;
		font-weight: 600;
		color: #888;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	.alert-item {
		background: #fffde7;
		border: 1px solid #f0e68c;
		border-radius: 8px;
		padding: 0.6rem 0.75rem;
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}
	.alert-item-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		font-size: 0.88rem;
		font-weight: 600;
	}
	.alert-date {
		font-size: 0.75rem;
		color: #999;
		font-weight: 400;
	}
	.alert-advice {
		font-size: 0.8rem;
		color: #555;
		line-height: 1.45;
		display: -webkit-box;
		-webkit-line-clamp: 3;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	/* Upload btn (mobile only) */
	.upload-btn {
		display: none;
		align-items: center;
		justify-content: center;
		width: 44px;
		height: 44px;
		border-radius: 50%;
		background: var(--cream);
		border: 1.5px solid var(--sage);
		cursor: pointer;
		font-size: 1.2rem;
		flex-shrink: 0;
		transition: background 0.15s;
	}
	.upload-btn:hover {
		background: var(--sage);
	}
	.upload-btn input[type="file"] {
		display: none;
	}

	/* Mobile scan strip (mobile only) */
	.mobile-scan-strip {
		display: none;
	}

	@media (max-width: 768px) {
		main {
			grid-template-columns: 1fr;
		}
		.scan-panel {
			display: none;
		}
		.upload-btn {
			display: flex;
		}
		.mobile-scan-strip {
			display: flex;
			flex-direction: column;
			gap: 0.5rem;
			padding: 0.6rem 1rem;
			background: var(--cream);
			border-top: 1.5px solid #e0e0e0;
		}
		.strip-row {
			display: flex;
			align-items: center;
			justify-content: space-between;
		}
		.strip-advisory {
			font-size: 0.82rem;
			line-height: 1.5;
			color: #555;
			max-height: 120px;
			overflow-y: auto;
		}
		header {
			padding: 0.6rem 1rem;
		}
		.brand {
			font-size: 1rem;
		}
	}
</style>
