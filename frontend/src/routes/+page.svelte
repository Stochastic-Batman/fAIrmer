<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	const API = 'http://localhost:8000';
	const REGIONS = ['აჭარა', 'გურია', 'იმერეთი', 'კახეთი', 'მცხეთა-მთიანეთი', 'რაჭა', 'სამეგრელო', 'სამცხე-ჯავახეთი', 'სვანეთი', 'შიდა ქართლი', 'ქვემო ქართლი', 'ქართლი', 'აფხაზეთი'];

	let mode = $state<'login' | 'signup'>('login');
	let username = $state('');
	let password = $state('');
	let region = $state('');
	let primaryCrops = $state('');
	let soilMetrics = $state('');
	let error = $state('');
	let loading = $state(false);

	onMount(() => {
		const raw = localStorage.getItem('farmer_session');
		if (raw) {
			const parsed = JSON.parse(raw);
			if (parsed.is_authenticated) goto('/barbale');
		}
	});

	async function submit() {
		error = '';
		loading = true;
		try {
			if (mode === 'login') {
				const res = await fetch(`${API}/api/login`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ username, password })
				});
				if (!res.ok) throw new Error('მომხმარებლის სახელი ან პაროლი არასწორია');
				const data = await res.json();
				localStorage.setItem('farmer_session', JSON.stringify({ ...data, is_authenticated: true }));
				goto('/barbale');
			} else {
				const res = await fetch(`${API}/api/register`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						username,
						password,
						region: region || null,
						primary_crops: primaryCrops || null,
						soil_metrics: soilMetrics || null
					})
				});
				if (!res.ok) {
					const err = await res.json();
					throw new Error(err.detail ?? 'Registration failed');
				}
				const data = await res.json();
				localStorage.setItem('farmer_session', JSON.stringify({ ...data, is_authenticated: true }));
				goto('/barbale');
			}
		} catch (e: any) {
			error = e.message;
		} finally {
			loading = false;
		}
	}
</script>

<div class="gate">
	<div class="left">
		<img src="/fAIrmer.png" alt="fAIrmer logo" class="logo" />
		<h1>fAIrmer</h1>
		<p>რჩევა, რომელიც მეზობელმაც კი არ იცის</p>
	</div>

	<div class="right">
		<div class="card">
			<div class="toggle">
				<button class:active={mode === 'login'} onclick={() => { mode = 'login'; error = ''; }}>შესვლა</button>
				<button class:active={mode === 'signup'} onclick={() => { mode = 'signup'; error = ''; }}>შექმენი ანგარიში</button>
			</div>

			<div class="fields">
				<input type="text" placeholder="მომხმარებლის სახელი" bind:value={username} />
				<input type="password" placeholder="პაროლი" bind:value={password} />

				{#if mode === 'signup'}
					<select bind:value={region}>
						<option value="">რეგიონი</option>
						{#each REGIONS as r}
							<option value={r}>{r}</option>
						{/each}
					</select>
					<input type="text" placeholder="ძირითადი კულტურა (მაგ. პომიდორი)" bind:value={primaryCrops} />
					<input type="text" placeholder="ნიადაგის მახასიათებლები (სურვილისამებრ)" bind:value={soilMetrics} />
				{/if}

				{#if error}
					<p class="error">{error}</p>
				{/if}

				<button class="cta" onclick={submit} disabled={loading}>
					{loading ? '...' : 'განაგრძე'}
				</button>
			</div>
		</div>
	</div>
</div>

<style>
	.gate {
		display: grid;
		grid-template-columns: 1fr 1fr;
		height: 100vh;
	}

	.left {
		background: var(--green);
		color: white;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		padding: 2rem;
		text-align: center;
	}

	.logo {
		width: 120px;
		height: 120px;
		object-fit: contain;
	}

	.left h1 {
		font-size: 2.5rem;
		font-weight: 700;
		letter-spacing: 0.05em;
	}

	.left p {
		font-size: 1rem;
		opacity: 0.85;
		max-width: 280px;
		line-height: 1.5;
	}

	.right {
		background: var(--cream);
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 2rem;
	}

	.card {
		background: white;
		border-radius: 12px;
		padding: 2rem;
		width: 100%;
		max-width: 380px;
		box-shadow: 0 4px 24px rgba(0,0,0,0.08);
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.toggle {
		display: grid;
		grid-template-columns: 1fr 1fr;
		border-radius: 8px;
		overflow: hidden;
		border: 1.5px solid var(--sage);
	}

	.toggle button {
		padding: 0.6rem;
		border: none;
		background: white;
		cursor: pointer;
		font-size: 0.95rem;
		color: var(--dark);
		transition: background 0.15s;
	}

	.toggle button.active {
		background: var(--green);
		color: white;
		font-weight: 600;
	}

	.fields {
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
	}

	.fields input,
	.fields select {
		padding: 0.65rem 0.85rem;
		border: 1.5px solid #ddd;
		border-radius: 8px;
		font-size: 0.95rem;
		width: 100%;
		outline: none;
		transition: border-color 0.15s;
	}

	.fields input:focus,
	.fields select:focus {
		border-color: var(--sage);
	}

	.error {
		color: #c0392b;
		font-size: 0.85rem;
	}

	.cta {
		padding: 0.75rem;
		background: var(--green);
		color: white;
		border: none;
		border-radius: 8px;
		font-size: 1.1rem;
		font-weight: 600;
		cursor: pointer;
		transition: background 0.15s;
		letter-spacing: 0.03em;
	}

	.cta:hover:not(:disabled) {
		background: var(--sage);
	}

	.cta:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	@media (max-width: 768px) {
		.gate {
			display: flex;
			flex-direction: column;
			height: auto;
			min-height: 100vh;
		}
		.left {
			padding: 1.25rem 1.5rem;
			gap: 0.4rem;
			flex-direction: row;
			justify-content: flex-start;
			text-align: left;
		}
		.logo {
			width: 44px;
			height: 44px;
		}
		.left h1 {
			font-size: 1.4rem;
		}
		.left p {
			display: none;
		}
		.right {
			flex: 1;
			padding: 2rem 1.25rem;
			align-items: stretch;
		}
		.card {
			max-width: 100%;
			box-shadow: none;
			border: 1.5px solid #e8e8e8;
		}
	}
</style>
