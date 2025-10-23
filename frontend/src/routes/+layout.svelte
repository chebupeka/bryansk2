<script lang="ts">
	import favicon from '$lib/assets/favicon.ico';
	import '../app.css';

	let { children } = $props();
</script>

<title>Честные Числа — Прозрачный ГСЧ</title>

<svelte:head>
	<link rel="icon" href={favicon} />
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0" />
	<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</svelte:head>

{@render children?.()}
