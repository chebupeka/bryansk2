<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import type PageData from './Analysis.svelte';
    import { api } from '$lib/services/api';

    const dispatch = createEventDispatcher();
    let fileInput: HTMLInputElement;
    let loading = false;
    let error = '';

    const handleUpload = async () => {
        if (!fileInput.files?.[0]) {
            error = 'Выберите файл (TXT/CSV с числами 0-99)';
            return;
        }
        loading = true;
        error = '';
        try {
            const result: PageData = await api.analyze(fileInput.files[0]);
            dispatch('analyzed', result);
        } catch (e: any) {
            error = e.message;
        } finally {
            loading = false;
        }
    };
</script>

<div class="p-4 border rounded dark:border-gray-600">
    <h3 class="font-bold mb-2">Загрузка внешней последовательности</h3>
    <input bind:this={fileInput} type="file" accept=".txt,.csv" class="mb-2" />
    <button on:click={handleUpload} disabled={loading} class="px-4 py-2 bg-green-600 text-white rounded">
        {loading ? 'Анализ...' : 'Анализировать'}
    </button>
    {#if error}
        <p class="text-red-500 mt-2">{error}</p>
    {/if}
</div>