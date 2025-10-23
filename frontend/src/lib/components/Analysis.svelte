<script lang="ts">
    import { onMount } from 'svelte';
    import type PageData from '../../routes/+page.svelte';  // Assume type

    export let data: PageData;

    $: userEntropy = data.user_entropy?.toFixed(4) || 'N/A';
    $: refEntropy = data.ref_entropy?.toFixed(4) || 'N/A';
    $: nistPassed = data.user_nist?.passed || 0;
    $: totalTests = data.user_nist?.total_tests || 0;

    const getSourceLabel = (source: string) => source === 'chaotic' ? 'Хаос' : source === 'noise' ? 'Шум (ОС)' : source;
</script>

{#if data.sequence && data.sequence.length > 0}
    <div class="p-4 rounded bg-gray-50 dark:bg-gray-800">
        <h3 class="font-bold mb-2">Результаты анализа</h3>
        <p><strong>Длина seq:</strong> {data.sequence.length}</p>
        <p><strong>Энтропия (user):</strong> {userEntropy} бит</p>
        <p><strong>Энтропия (эталон):</strong> {refEntropy} бит</p>
        <p><strong>NIST (user):</strong> {nistPassed}/{totalTests} пройдено</p>

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
            {#each data.comparison?.results || [] as test}
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