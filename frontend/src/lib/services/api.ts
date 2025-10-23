const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

export const api = {
	generate: async (source: 'chaotic' | 'noise', params: Record<string, any>) => {
		const url = new URL(`${API}/generate/${source}`);
		Object.entries(params).forEach(([k, v]) => url.searchParams.append(k, v.toString()));
		const res = await fetch(url);
		if (!res.ok) throw new Error(`HTTP ${res.status}`);
		return res.json();
	},
	checkHash: async (hash: string) => {
		const res = await fetch(`${API}/check_hash/${hash}`);
		if (!res.ok) throw new Error(`HTTP ${res.status}`);
		return res.json();
	},
	nist: async (id: number) => {
		const res = await fetch(`${API}/nist/${id}`);
		if (!res.ok) throw new Error(`HTTP ${res.status}`);
		return res.json();
	},
	analyze: async (file: File) => {
		const formData = new FormData();
		formData.append('file', file);
		const res = await fetch(`${API}/analyze`, {
			method: 'POST',
			body: formData
		});
		if (!res.ok) throw new Error(`HTTP ${res.status}`);
		return res.json();
	}
};