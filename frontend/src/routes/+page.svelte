<script>
    import { onMount } from 'svelte';
    import Chart from 'chart.js/auto';

    let sequence = [];
    let entropy = 0;
    let hash = '';
    let chart;

    async function generate(source) {
        const res = await fetch(`http://localhost:8000/generate/${source}?n=50`);
        const data = await res.json();
        sequence = data.sequence;
        entropy = data.entropy;
        hash = data.hash;

        // Визуализация
        const ctx = document.getElementById('chart');
        if (chart) chart.destroy();
        chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: sequence.map((_, i) => i),
                datasets: [{ label: 'Sequence', data: sequence }]
            },
            options: { scales: { y: { beginAtZero: true } } }
        });
    }
</script>

<main>
    <h1>Демо ГСЧ и Энтропии</h1>
    <button on:click={() => generate('chaotic')}>Генерировать из Хаоса</button>
    <button on:click={() => generate('noise')}>Генерировать из Шума</button>
    <p>Последовательность: {sequence.join(', ')}</p>
    <p>Энтропия: {entropy.toFixed(2)} бит</p>
    <p>Хэш для верификации: {hash}</p>
    <canvas id="chart" width="400" height="200"></canvas>
</main>