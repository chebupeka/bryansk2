import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
    plugins: [sveltekit()],
    define: {
        'import.meta.env.VITE_API_URL': JSON.stringify(process.env.VITE_API_URL)
    }
});