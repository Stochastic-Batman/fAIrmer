<script lang="ts">
	let { children } = $props();
</script>

<svelte:head>
	<title>fAIrmer</title>
	<link rel="icon" type="image/png" href="/fAIrmer.png" />
	<link rel="preconnect" href="https://fonts.googleapis.com" />
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous" />
	<link href="https://fonts.googleapis.com/css2?family=MedievalSharp&display=swap" rel="stylesheet" />
</svelte:head>

{@render children()}

<style>
	:global(*, *::before, *::after) {
		box-sizing: border-box;
		margin: 0;
		padding: 0;
	}

	:global(:root) {
		--green:  #2F6B3F;
		--sage:   #7FB77E;
		--gold:   #F7C85C;
		--cream:  #FFF6C0;
		--dark:   #1a1a1a;
		font-family: 'MedievalSharp', 'Segoe UI', system-ui, sans-serif;
	}

	:global(body) {
		background: var(--cream);
		color: var(--dark);
	}
</style>
