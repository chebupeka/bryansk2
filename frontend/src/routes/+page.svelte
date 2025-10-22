<script lang="ts">
    import { onMount } from 'svelte';
    import { browser } from '$app/environment';
    import Chart from 'chart.js/auto';

    let chart: Chart;
    let data = { sequence: [], entropy: 0, id: null, hash: '', source: 'chaotic' as 'chaotic' | 'noise' };
    let loading = false;
    let chartType: 'line' | 'bar' = 'line';
    let darkMode = true;
    let nist = null;
    const API = 'http://127.0.0.1:8000';

    onMount(() => {
        if (browser) {
            const savedTheme = localStorage.getItem('theme');
            darkMode = savedTheme ? JSON.parse(savedTheme) : true;
            const savedSource = localStorage.getItem('lastSource') as 'chaotic' | 'noise' | null;
            const savedType = localStorage.getItem('lastChartType') as 'line' | 'bar' | null;
            if (savedSource) data.source = savedSource;
            if (savedType) chartType = savedType;
        }
        fetchSeq(data.source);
    });

    const toggleTheme = () => {
        darkMode = !darkMode;
        if (browser) localStorage.setItem('theme', JSON.stringify(darkMode));
        updateChart();
    };

    const fetchSeq = async (src: 'chaotic' | 'noise') => {
        data.source = src;
        if (browser) localStorage.setItem('lastSource', src);
        loading = true;
        nist = null;
        try {
            const res = await fetch(`${API}/generate/${src}?n=100`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const json = await res.json();
            data = { ...data, ...json, source: src };
            fetchNist();
            updateChart();
        } catch (e: any) {
            console.error(e);
            alert('Ошибка: ' + e.message);
        } finally {
            loading = false;
        }
    };

    const fetchNist = async () => {
        if (!data.id) return;
        try {
            const res = await fetch(`${API}/nist/${data.id}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            nist = await res.json();
        } catch (e: any) {
            console.error(e);
            alert('NIST ошибка: ' + e.message);
        }
    };

    const verify = async () => {
        if (!data.id) return;
        try {
            const res = await fetch(`${API}/verify/${data.id}`);
            const v = await res.json();
            alert(`Верифицировано!\nЭнтропия: ${v.entropy.toFixed(4)}`);
        } catch {
            alert('Ошибка верификации');
        }
    };

    const updateChart = () => {
        const ctx = document.getElementById('chart')?.getContext('2d');
        if (!ctx || !data.sequence.length) return;
        chart?.destroy();

        const isBar = chartType === 'bar';
        const color = data.source === 'chaotic' ? '#60a5fa' : '#34d399';

        chart = new Chart(ctx, {
            type: chartType,
            data: {
                labels: data.sequence.map((_, i) => i),
                datasets: [{
                    label: data.source === 'chaotic' ? 'Хаос' : 'Шум (ОС)',
                    data: data.sequence,
                    borderColor: color,
                    backgroundColor: isBar ? `${color}40` : 'transparent',
                    borderWidth: isBar ? 1 : 2,
                    barThickness: 2,
                    tension: 0.1,
                    pointRadius: isBar ? 0 : 1.5
                }]
            },
            options: {
                responsive: true,
                animation: { duration: 800 },
                plugins: {
                    title: { display: true, text: `Энтропия: ${data.entropy.toFixed(4)} бит`, color: darkMode ? '#e5e7eb' : '#1f2937' },
                    legend: { labels: { color: darkMode ? '#9ca3af' : '#374151' } }
                },
                scales: {
                    x: { ticks: { color: darkMode ? '#9ca3af' : '#374151' }, grid: { color: darkMode ? '#374151' : '#d1d5db' } },
                    y: { min: 0, max: 100, ticks: { color: darkMode ? '#9ca3af' : '#374151' }, grid: { color: darkMode ? '#374151' : '#d1d5db' } }
                }
            }
        });
    };

    $: if (browser && chartType) {
        localStorage.setItem('lastChartType', chartType);
        updateChart();
    }
</script>

<main class="{darkMode ? 'bg-gray-900 text-gray-100' : 'bg-white text-gray-900'} min-h-screen p-4 md:p-6 transition-colors">
    <div class="max-w-4xl mx-auto">
        <button on:click={toggleTheme} class="mb-4 px-4 py-2 {darkMode ? 'bg-gray-700 text-gray-100' : 'bg-gray-200 text-gray-900'} rounded">
            {darkMode ? 'Светлая тема' : 'Тёмная тема'}
        </button>

        <h1 class="text-3xl font-bold mb-6">ГСЧ: Хаос + Шум</h1>

        <div class="flex gap-4 mb-6">
            <button on:click={() => fetchSeq('chaotic')} class="px-4 py-2 bg-blue-600 text-white rounded">Хаос</button>
            <button on:click={() => fetchSeq('noise')} class="px-4 py-2 bg-green-600 text-white rounded">Шум (ОС)</button>
            {#if data.id}
                <button on:click={verify} class="px-4 py-2 bg-purple-600 text-white rounded">Верифицировать #{data.id}</button>
            {/if}
        </div>

        <div class="flex gap-4 mb-6">
            <label>
                <input type="radio" bind:group={chartType} value="line" /> Линия
            </label>
            <label>
                <input type="radio" bind:group={chartType} value="bar" /> Гистограмма
            </label>
        </div>

        {#if loading}
            <div class="flex items-center justify-center py-12">
                <div class="animate-spin rounded-full h-10 w-10 border-4 border-blue-500 border-t-transparent"></div>
                <span class="ml-4">Генерация...</span>
            </div>
        {:else}
            <div class="{darkMode ? 'bg-gray-800 text-gray-100' : 'bg-gray-100 text-gray-900'} p-4 rounded mb-6">
                <p><strong>Источник:</strong> {data.source}</p>
                <p><strong>Энтропия:</strong> {data.entropy.toFixed(4)} бит</p>
                <p><strong>Хэш:</strong> {data.hash.slice(0, 16)}...</p>
            </div>

            <canvas id="chart" class="w-full h-64"></canvas>

            {#if nist}
                <div class="{darkMode ? 'bg-gray-800 text-gray-100' : 'bg-gray-100 text-gray-900'} p-4 rounded mt-6">
                    <p class="font-bold">NIST: {nist.passed}/{nist.total_tests} пройдено</p>
                    {#each nist.results as test}
                        <p>{test.test}: {test.passed ? 'PASS' : 'FAIL'} {test.score ? "(score = " + test.score + ")" : ''}</p>
                    {/each}
                </div>
            {/if}
        {/if}
    </div>
</main>

<style>
    :global(body) { margin: 0; font-family: system-ui; }
</style>