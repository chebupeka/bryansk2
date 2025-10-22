<script lang="ts">
    import { onMount } from 'svelte';
    import { browser } from '$app/environment';
    import Chart from 'chart.js/auto';

    let chart: Chart;
    let data = {
        sequence: [],
        entropy: 0,
        id: null,
        hash: '',
        source: 'chaotic' as 'chaotic' | 'noise',
        generatedSource: '',
        generatedMin: 0,
        generatedMax: 99,
        generatedDuplicates: true
    };
    let loading = false;
    let chartType: 'line' | 'bar' = 'line';
    let darkMode = true;
    let nist = null;
    let minVal = 0;
    let maxVal = 99;
    let allowDuplicates = true;
    let hashInput = '';  // For hash verification
    const API = 'http://127.0.0.1:8000';

    // Reactive validation for sliders
    $: if (minVal > maxVal) maxVal = minVal;

    // Reactive chart update on data.sequence change
    $: if (data.sequence.length > 0) {
        setTimeout(() => updateChart(), 0);  // Defer for DOM ready
    }

    // Reactive for chartType change only
    $: if (chartType && data.sequence.length > 0) {
        updateChart();
    }

    onMount(() => {
        if (browser) {
            const savedTheme = localStorage.getItem('theme');
            darkMode = savedTheme ? JSON.parse(savedTheme) : true;
            applyTheme();
            const savedSource = localStorage.getItem('lastSource') as 'chaotic' | 'noise' | null;
            const savedType = localStorage.getItem('lastChartType') as 'line' | 'bar' | null;
            const savedMin = localStorage.getItem('lastMin');
            const savedMax = localStorage.getItem('lastMax');
            const savedDuplicates = localStorage.getItem('lastDuplicates');
            if (savedSource) data.source = savedSource;
            if (savedType) chartType = savedType;
            if (savedMin) minVal = parseInt(savedMin);
            if (savedMax) maxVal = parseInt(savedMax);
            if (savedDuplicates !== null) allowDuplicates = JSON.parse(savedDuplicates);
        }
        // No auto-fetch here!
    });

    const applyTheme = () => {
        if (browser) {
            const html = document.documentElement;
            if (darkMode) {
                html.classList.add('dark');
            } else {
                html.classList.remove('dark');
            }
        }
    };

    const toggleTheme = () => {
        darkMode = !darkMode;
        if (browser) localStorage.setItem('theme', JSON.stringify(darkMode));
        applyTheme();
        if (data.sequence.length > 0) updateChart();
    };

    const fetchSeq = async (src: 'chaotic' | 'noise') => {
        if (minVal > maxVal) {
            alert('Минимальное значение не может быть больше максимального!');
            return;
        }
        data.source = src;
        if (browser) {
            localStorage.setItem('lastSource', src);
            localStorage.setItem('lastMin', minVal.toString());
            localStorage.setItem('lastMax', maxVal.toString());
            localStorage.setItem('lastDuplicates', JSON.stringify(allowDuplicates));
        }
        loading = true;
        nist = null;
        try {
            const params = new URLSearchParams({
                n: '100',
                min_val: minVal.toString(),
                max_val: maxVal.toString(),
                allow_duplicates: allowDuplicates.toString()
            });
            const res = await fetch(`${API}/generate/${src}?${params}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const json = await res.json();
            data = {
                ...data,
                ...json,
                source: src,
                generatedSource: json.generatedSource,
                generatedMin: json.generatedMin,
                generatedMax: json.generatedMax,
                generatedDuplicates: json.generatedDuplicates
            };
            hashInput = data.hash;  // Auto-fill hash input
            fetchNist();
            // Chart updates reactively, but force if needed
            setTimeout(() => updateChart(), 100);
        } catch (e: any) {
            console.error(e);
            alert('Ошибка: ' + e.message);
        } finally {
            loading = false;
        }
    };

    const checkByHash = async () => {
        if (!hashInput) {
            alert('Введите хэш последовательности!');
            return;
        }
        loading = true;
        nist = null;
        try {
            const res = await fetch(`${API}/check_hash/${hashInput}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const json = await res.json();
            data = {
                ...data,
                ...json,
                generatedSource: json.generatedSource,
                generatedMin: json.generatedMin,
                generatedMax: json.generatedMax,
                generatedDuplicates: json.generatedDuplicates
            };
            data.source = 'verified' as any;  // For UI only, generated fixed
            fetchNist();
            // Chart updates reactively, but force if needed
            setTimeout(() => updateChart(), 100);
        } catch (e: any) {
            console.error(e);
            alert('Ошибка проверки: ' + e.message);
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

    const generateNow = () => {
        fetchSeq(data.source);
    };

    // Auto-select source on click, but don't auto-gen
    const selectSource = (src: 'chaotic' | 'noise') => {
        data.source = src;
    };

    const updateChart = () => {
        const ctx = document.getElementById('chart')?.getContext('2d');
        if (!ctx || !data.sequence.length) return;
        if (chart) chart.destroy();

        const isBar = chartType === 'bar';
        const color = data.generatedSource === 'chaotic' ? '#60a5fa' : data.generatedSource === 'noise' ? '#34d399' : '#8b5cf6';  // Purple for verified
        const textColor = darkMode ? '#e5e7eb' : '#1f2937';
        const tickColor = darkMode ? '#9ca3af' : '#374151';
        const gridColor = darkMode ? '#374151' : '#d1d5db';

        chart = new Chart(ctx, {
            type: chartType,
            data: {
                labels: data.sequence.map((_, i) => i),
                datasets: [{
                    label: data.generatedSource === 'chaotic' ? 'Хаос' : data.generatedSource === 'noise' ? 'Шум (ОС)' : 'Верифицировано',
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
                    title: { display: true, text: `Энтропия: ${data.entropy.toFixed(4)} бит`, color: textColor },
                    legend: { labels: { color: tickColor } }
                },
                scales: {
                    x: {
                        ticks: { color: tickColor },
                        grid: { color: gridColor },
                        min: 0,
                        max: data.sequence.length - 1
                    },
                    y: {
                        min: 0,
                        max: Math.max(...data.sequence) + 10 || 100,
                        ticks: { color: tickColor },
                        grid: { color: gridColor }
                    }
                }
            }
        });
    };

    $: if (browser && chartType) {
        localStorage.setItem('lastChartType', chartType);
    }
</script>

<main class="min-h-screen p-4 md:p-6 transition-colors duration-300">
    <div class="max-w-4xl mx-auto">
        <button on:click={toggleTheme} class="mb-4 px-4 py-2 rounded transition-colors bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200">
            {darkMode ? 'Светлая тема' : 'Тёмная тема'}
        </button>

        <h1 class="text-3xl font-bold mb-6">ГСЧ: Хаос + Шум</h1>

        <div class="flex gap-4 mb-6">
            <button on:click={() => selectSource('chaotic')} class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition {data.source === 'chaotic' ? 'ring-2 ring-blue-300' : ''}">Хаос</button>
            <button on:click={() => selectSource('noise')} class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition {data.source === 'noise' ? 'ring-2 ring-green-300' : ''}">Шум (ОС)</button>
            <button on:click={generateNow} disabled={loading} class="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 transition disabled:opacity-50 disabled:cursor-not-allowed">
                {loading ? 'Генерация...' : 'Генерировать'}
            </button>
        </div>

        <!-- Hash verification section -->
        <div class="mb-6 p-4 rounded bg-gray-50 dark:bg-gray-800">
            <label class="block text-sm font-medium mb-2">Проверить по хэшу:</label>
            <div class="flex gap-2">
                <input bind:value={hashInput} placeholder="Введите полный хэш (SHA-256)..." class="flex-1 px-3 py-2 border rounded dark:bg-gray-700 dark:border-gray-600 dark:text-white" />
                <button on:click={checkByHash} disabled={loading} class="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700 transition disabled:opacity-50">
                    Проверить
                </button>
            </div>
            {#if data.hash && data.sequence.length > 0}
                <p class="text-xs mt-1 text-gray-500 dark:text-gray-400">Текущий хэш: {data.hash.slice(0, 16)}... (скопируйте для проверки)</p>
            {/if}
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div>
                <label class="block text-sm font-medium mb-2">От: {minVal}</label>
                <input type="range" bind:value={minVal} min="0" max="99" class="w-full" />
            </div>
            <div>
                <label class="block text-sm font-medium mb-2">До: {maxVal}</label>
                <input type="range" bind:value={maxVal} min="0" max="99" class="w-full" />
            </div>
            <div class="flex items-center">
                <input type="checkbox" bind:checked={allowDuplicates} id="duplicates" class="mr-2" />
                <label for="duplicates" class="text-sm">Разрешить повторы</label>
            </div>
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
        {:else if data.sequence.length === 0}
            <div class="p-4 rounded mb-6 transition-colors text-center text-gray-500 dark:text-gray-400">
                <p>Выберите источник, настройте параметры и нажмите "Генерировать" для создания последовательности.</p>
            </div>
            <canvas id="chart" class="w-full h-64 bg-gray-100 dark:bg-gray-800 rounded opacity-50"></canvas>
        {:else}
            <div class="p-4 rounded mb-6 transition-colors bg-gray-50 dark:bg-gray-800">
                <p><strong>Источник:</strong> {data.generatedSource === 'verified' ? 'Верифицировано' : data.generatedSource}</p>
                <p><strong>Диапазон:</strong> {data.generatedMin} - {data.generatedMax}</p>
                <p><strong>Повторы:</strong> {data.generatedDuplicates ? 'Да' : 'Нет'}</p>
                <p><strong>Энтропия:</strong> {data.entropy.toFixed(4)} бит</p>
                <p><strong>Хэш:</strong> {data.hash.slice(0, 16)}...</p>
            </div>

            <canvas id="chart" class="w-full h-64"></canvas>

            {#if nist}
                <div class="p-4 rounded mt-6 transition-colors bg-gray-50 dark:bg-gray-800">
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
    :global(body) {
        margin: 0;
        font-family: system-ui;
        background-color: #f9fafb;
        color: #111827;
        transition: background-color 0.3s, color 0.3s;
    }
    :global(html.dark body) {
        background-color: #111827;
        color: #f9fafb;
    }
    :global(html.dark input[type="range"]::-webkit-slider-thumb) {
        background: #e5e7eb;
    }
    :global(html.dark input[type="range"]::-moz-range-thumb) {
        background: #e5e7eb;
    }
    :global(html.dark .bg-gray-50) { background-color: #374151; }
    :global(html.dark .bg-gray-100) { background-color: #4b5563; }
    :global(html.dark .text-gray-500) { color: #9ca3af; }
    :global(html.dark .text-gray-400) { color: #9ca3af; }
    /* Добавь больше классов по мере нужды; Tailwind не обязателен */
</style>