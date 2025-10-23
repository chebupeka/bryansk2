<script lang="ts">
	import { onMount } from 'svelte';
	import { browser } from '$app/environment';
	import Chart from 'chart.js/auto';
	import Upload from '$lib/components/Upload.svelte';
	import ToggleThemeButton from '$lib/components/ToggleThemeButton.svelte';

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
	let analysisData: any = null;
	let loading = false;
	let chartType: 'line' | 'bar' = 'line';
	let darkMode = true;
	let nist = null;
	let minVal = 0;
	let maxVal = 99;
	let allowDuplicates = true;
	let hashInput = '';
	import { api } from '$lib/services/api';

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

	const applyTheme = () => {
		if (browser) {
			const body = document.body;
			if (darkMode) {
				body.classList.add('dark-mode');
			} else {
				body.classList.remove('dark-mode');
			}
		}
	};

	const toggleTheme = () => {
		darkMode = !darkMode;
		if (browser) localStorage.setItem('theme', JSON.stringify(darkMode));
		applyTheme();
		if (data.sequence.length > 0) updateChart();
	};

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
	});


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
			const params = {
				n: 100,
				min_val: minVal,
				max_val: maxVal,
				allow_duplicates: allowDuplicates
			};
			const json = await api.generate(src, params);
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
			nist = await api.nist(data.id);
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
			const json = await api.checkHash(hashInput);
			data = {
				...data,
				...json,
				generatedSource: json.generatedSource,
				generatedMin: json.generatedMin,
				generatedMax: json.generatedMax,
				generatedDuplicates: json.generatedDuplicates
			};
			data.source = 'verified' as any;  // For UI only, generated fixed
			nist = await api.nist(data.id);
			// Chart updates reactively, but force if needed
			setTimeout(() => updateChart(), 100);
		} catch (e: any) {
			console.error(e);
			alert('Ошибка проверки: ' + e.message);
		} finally {
			loading = false;
		}
	};

	const generateNow = () => {
		fetchSeq(data.source);
	};

	// Auto-select source on click, but don't auto-gen
	const selectSource = (src: 'chaotic' | 'noise') => {
		data.source = src;
	};

	// Handle upload analyzed
	const handleAnalyzed = (e: CustomEvent) => {
		analysisData = e.detail;
	};

	const updateChart = () => {
		const ctx = document.getElementById('chart')?.getContext('2d');
		if (!ctx || !data.sequence.length) return;
		if (chart) chart.destroy();

		const isBar = chartType === 'bar';
		const color = data.source === 'chaotic' ? '#3b82f6' : '#10b981';

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
					tension: 0.1,
					pointRadius: isBar ? 0 : 2
				}]
			},
			options: {
				responsive: true,
				maintainAspectRatio: false,
				plugins: {
					legend: {
						labels: {
							color: darkMode ? '#f9fafb' : '#111827'
						}
					}
				},
				scales: {
					x: {
						ticks: {
							color: darkMode ? '#9ca3af' : '#6b7280'
						},
						grid: {
							color: darkMode ? '#374151' : '#e5e7eb'
						}
					},
					y: {
						ticks: {
							color: darkMode ? '#9ca3af' : '#6b7280'
						},
						grid: {
							color: darkMode ? '#374151' : '#e5e7eb'
						}
					}
				}
			}
		});
	};

	$: if (browser && chartType) {
		localStorage.setItem('lastChartType', chartType);
	}
</script>

<div>
	<div class="container">
		<header>
			<h1>ГСЧ: Хаос + Шум</h1>
			<ToggleThemeButton {toggleTheme} {darkMode} />
		</header>

		<div class="card">
			<h2 class="card-title">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
				</svg>
				Источник данных
			</h2>
			<div class="source-buttons">
				<button on:click={() => selectSource('chaotic')} class="btn btn-primary">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
									d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4" />
					</svg>
					Хаос
				</button>
				<button on:click={() => selectSource('noise')} class="btn btn-success">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
									d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
					</svg>
					Шум (ОС)
				</button>
				<button on:click={generateNow} disabled={loading} class="btn btn-primary">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
					</svg>
					{loading ? 'Генерация...' : 'Генерировать'}
				</button>
			</div>

			<div class="hash-section">
				<label>
					Проверить по хэшу:
				</label>
				<div class="hash-input-container">
					<input type="text" bind:value={hashInput} placeholder="Введите полный хэш (SHA-256)...">
					<button on:click={checkByHash} disabled={loading} class="btn btn-warning">
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
										d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
						</svg>
						Проверить
					</button>
				</div>
				<div class="hash-hint">
					{#if data.hash && data.sequence.length > 0}
						<p>Текущий хэш: {data.hash.slice(0, 16)}... (скопируйте для проверки)</p>
					{/if}
				</div>
			</div>
		</div>

		<div class="card">
			<h2 class="card-title">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
								d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
				</svg>
				Параметры генерации
			</h2>
			<div class="controls-grid">
				<div class="control-group">
					<label>
						От: {minVal}
						<div class="range-container">
							<span class="range-value">0</span>
							<input class="w-full" type="range" bind:value={minVal} min="0" max="99">
							<span class="range-value">99</span>
						</div>
					</label>
				</div>
				<div class="control-group">
					<label>
						До: {maxVal}
						<div class="range-container">
							<span class="range-value">0</span>
							<input class="w-full" type="range" bind:value={maxVal} min="0" max="99">
							<span class="range-value">99</span>
						</div>
					</label>
				</div>
				<div class="control-group">
					<label>
						Дополнительные настройки
						<div class="checkbox-container">
							<input type="checkbox" bind:checked={allowDuplicates} id="duplicates" />
							<label for="allowDuplicates">Разрешить повторы</label>
						</div>
					</label>
				</div>
			</div>
		</div>

		<div class="card">
			<h2 class="card-title">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
								d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
				</svg>
				Визуализация
			</h2>
			<div class="chart-type-selector">
				<label for="lineButton">
					<div class="chart-type-btn {chartType === 'line' ? 'btn-active active' : null}" data-type="line">
						Линия
						<input id="lineButton" type="radio" bind:group={chartType} value="line"
									 style="display: none; visibility: hidden;" />

					</div>
				</label>
				<label for="barButton">
					<div class="chart-type-btn {chartType === 'bar' ? 'btn-active active' : null}" data-type="bar">
						Гистограмма
						<input id="barButton" type="radio" bind:group={chartType} value="bar"
									 style="display: none; visibility: hidden;" />
					</div>
				</label>
			</div>
			<div class="chart-container">
				<canvas id="chart"></canvas>
				<div class="empty-state" style="display: {data.sequence.length === 0 ? 'flex' : 'none'} ">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
						<path
							d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
						<polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
						<line x1="12" y1="22.08" x2="12" y2="12"></line>
					</svg>
					<p>Выберите источник, настройте параметры и нажмите "Генерировать" для создания последовательности.</p>
				</div>
				{#if loading}
					<div class="loading" id="loadingState" style="display: none;">
						<div class="spinner"></div>
						<p>Генерация...</p>
					</div>
				{/if}
			</div>
		</div>

		<div class="card" style="display: {data.sequence.length !== 0 ? 'block' : 'none'}">
			<h2 class="card-title">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
								d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
				</svg>
				Результаты
			</h2>
			{#if !loading}
				<div class="stats-grid">
					<div class="stat-card">
						<div class="stat-label">Источник</div>
						<div class="stat-value"
								 id="sourceValue">{data.generatedSource === 'verified' ? 'Верифицировано' : data.generatedSource}</div>
					</div>
					<div class="stat-card">
						<div class="stat-label">Диапазон</div>
						<div class="stat-value" id="rangeValue">{data.generatedMin} - {data.generatedMax}</div>
					</div>
					<div class="stat-card">
						<div class="stat-label">Повторы</div>
						<div class="stat-value" id="duplicatesValue">{data.generatedDuplicates ? 'Да' : 'Нет'}</div>
					</div>
					<div class="stat-card">
						<div class="stat-label">Энтропия</div>
						<div class="stat-value" id="entropyValue">{data.entropy.toFixed(4)} бит</div>
					</div>
					<div class="stat-card">
						<div class="stat-label">Хэш</div>
						<div class="stat-value" id="hashValue">{data.hash.slice(0, 16)}...</div>
					</div>
				</div>
			{:else}
				<div class="stats-grid">
					<div class="stat-card">
						<div class="stat-label">Источник</div>
						<div class="stat-value" id="sourceValue">-</div>
					</div>
					<div class="stat-card">
						<div class="stat-label">Диапазон</div>
						<div class="stat-value" id="rangeValue">-</div>
					</div>
					<div class="stat-card">
						<div class="stat-label">Повторы</div>
						<div class="stat-value" id="duplicatesValue">-</div>
					</div>
					<div class="stat-card">
						<div class="stat-label">Энтропия</div>
						<div class="stat-value" id="entropyValue">-</div>
					</div>
				</div>
			{/if}
		</div>

		<div class="card" id="nistCard" style="display: {data.sequence.length !== 0 ? 'block' : 'none'}">
			<h2 class="card-title">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
								d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
				</svg>
				NIST Тесты
			</h2>
			{#if nist}
				<div class="nist-results">
					<div class="nist-header">
						<div class="nist-score" id="nistScore">{nist.passed}/{nist.total_tests} пройдено</div>
					</div>
					<div class="nist-tests" id="nistTests">
						{#each nist.results as test}
							<div class="nist-test">
								<div class="test-name">
									{test.test}
								</div>
								<div class="test-result {test.passed ? 'test-pass' : 'test-fail'}">
									{test.passed ? 'PASS' : 'FAIL'}
									{test.score ? "(score = " + test.score + ")" : ''}
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		</div>

		<div class="card">
			<h2 class="card-title">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
								d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
				</svg>
				Загрузка последовательности
			</h2>
			<Upload on:analyzed={handleAnalyzed} />
		</div>
		{ #if analysisData }
			<div class="card">
				<h2 class="card-title">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
									d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
					</svg>
					Результаты анализа
				</h2>
				<div class="stats-grid">
					<div class="stat-card">
						<div class="stat-label">Длина seq</div>
						<div class="stat-value">{analysisData.sequence.length}</div>
					</div>
					<div class="stat-card">
						<div class="stat-label">Энтропия (user)</div>
						<div class="stat-value">{analysisData.user_entropy} бит</div>
					</div>
					<div class="stat-card">
						<div class="stat-label">Энтропия (эталон)</div>
						<div class="stat-value">{analysisData.ref_entropy} бит</div>
					</div>
					<div class="stat-card">
						<div class="stat-label">NIST (user)</div>
						<div class="stat-value">{analysisData.user_nist.passed}/{analysisData.user_nist.total_tests} пройдено</div>
					</div>
				</div>
				{#if analysisData.sequence && analysisData.sequence.length > 0}
					<div class="p-4 rounded bg-gray-50 dark:bg-gray-800">

						<table class="w-full mt-4 border-collapse border dark:border-gray-600">
							<thead>
							<tr class="bg-gray-200 dark:bg-gray-700">
								<th class="border p-2">Тест</th>
								<th class="border p-2">User PASS</th>
								<th class="border p-2">Эталон PASS</th>
								<th class="border p-2">User Score</th>
								<th class="border p-2">Эталон Score</th>
							</tr>
							</thead>
							<tbody>
							{#each analysisData.comparison?.results || [] as test}
								<tr>
									<td class="border p-2">{test.test}</td>
									<td class="border p-2">{test.user_pass ? 'PASS' : 'FAIL'}</td>
									<td class="border p-2">{test.ref_pass ? 'PASS' : 'FAIL'}</td>
									<td class="border p-2">{test.user_score || 'N/A'}</td>
									<td class="border p-2">{test.ref_score || 'N/A'}</td>
								</tr>
							{/each}
							</tbody>
						</table>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>