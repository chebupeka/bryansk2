<script lang="ts">
    import { onMount } from 'svelte';
    import { Chart } from 'chart.js';

    let chart: Chart;
    let sequence = [];
    let entropy = 0;
    let source = 'chaotic';
    let id = null;
    let hash = '';
    let loading = false;

    const API_URL = 'http://127.0.0.1:8000';

    async function generate() {
        loading = true;
        try {
            const res = await fetch(`${API_URL}/generate/${source}?n=100`);
            const data = await res.json();
            sequence = data.sequence;
            entropy = data.entropy.toFixed(4);
            id = data.id;
            hash = data.hash;

            updateChart();
        } catch (e) {
            alert('Ошибка: ' + e);
        } finally {
            loading = false;
        }
    }

    async function verify() {
        if (!id) return;
        try {
            const res = await fetch(`${API_URL}/verify/${id}`);
            const data = await res.json();
            alert(`Верификация прошла!\nЭнтропия: ${data.entropy.toFixed(4)}`);
        } catch (e) {
            alert('Ошибка верификации');
        }
    }

    function updateChart() {
        const ctx = document.getElementById('chart').getContext('2d');
        if (chart) chart.destroy();

        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: sequence.map((_, i) => i),
                datasets: [{
                    label: `Последовательность (${source})`,
                    data: sequence,
                    borderColor: source === 'chaotic' ? '#3b82f6' : '#10b981',
                    backgroundColor: 'rgba(0,0,0,0)',
                    tension: 0.1,
                    pointRadius: 2
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { min: 0, max: 100 },
                    x: { title: { display: true, text: 'Индекс' } }
                },
                plugins: {
                    title: { display: true, text: `Энтропия: ${entropy} бит` },
                    legend: { display: true }
                }
            }
        });
    }

    onMount(() => {
        generate();
    });
</script>

<main class="p-8 max-w-4xl mx-auto">
    <h1 class="text-3xl font-bold mb-6">ГСЧ: Хаос + Шум</h1>

    <div class="flex gap-4 mb-6">
        <button
                on:click={() => { source = 'chaotic'; generate(); }}
                class="px-6 py-3 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
            Хаос
        </button>
        <button
                on:click={() => { source = 'noise'; generate(); }}
                class="px-6 py-3 bg-green-600 text-white rounded hover:bg-green-700"
        >
            Шум (по ОС)
        </button>
        {#if id}
            <button
                    on:click={verify}
                    class="px-6 py-3 bg-purple-600 text-white rounded hover:bg-purple-700"
            >
                Верифицировать #{id}
            </button>
        {/if}
    </div>

    {#if loading}
        <p class="text-gray-600">Генерация...</p>
    {:else}
        <div class="bg-gray-50 p-4 rounded mb-4">
            <p><strong>Источник:</strong> {source}</p>
            <p><strong>Энтропия:</strong> {entropy} бит</p>
            <p><strong>Хэш:</strong> {hash.slice(0, 16)}...</p>
        </div>
    {/if}

    <canvas id="chart" class="w-full h-96 border rounded"></canvas>
</main>

<style>
    :global(body) { font-family: system-ui, sans-serif; background: #f9fafb; }
</style>