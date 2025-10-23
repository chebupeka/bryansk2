<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import { api } from '$lib/services/api';

    const dispatch = createEventDispatcher();
    let fileInput: HTMLInputElement = null;
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
            const result = await api.analyze(fileInput.files[0]);
            dispatch('analyzed', result);
        } catch (e: any) {
            error = e.message;
        } finally {
            loading = false;
        }
    };
</script>

<div class="source-buttons">
    <label for="file-upload" id="file-name" class="btn btn-primary">
        {#if error}
            <p class="text-red-500 mt-2">{error}</p>
        {:else}
            Загрузить файл
        {/if}
    </label>
    <input bind:this={fileInput} style="visibility: hidden; display: none" id="file-upload" type="file" accept=".txt,.csv" />
    <button style="border: none; outline: none;" on:click={handleUpload} disabled={loading} class="btn btn-success">
        {loading ? 'Анализ...' : 'Анализировать'}
    </button>
</div>