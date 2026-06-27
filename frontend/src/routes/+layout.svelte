<script lang="ts">
	let { children } = $props();
</script>

<svelte:head>
	<title>fAIrmer</title>
	<link rel="icon" type="image/png" href="/fAIrmer.png" />
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
		font-family: 'Segoe UI', system-ui, sans-serif;
	}

	:global(body) {
		background: var(--cream);
		color: var(--dark);
	}
</style>
