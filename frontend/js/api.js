const BASE = '/api';

async function request(method, path, body = null) {
    const opts = { method, headers: {} };
    if (body && !(body instanceof FormData)) {
        opts.headers['Content-Type'] = 'application/json';
        opts.body = JSON.stringify(body);
    } else if (body instanceof FormData) {
        opts.body = body;
    }
    const resp = await fetch(BASE + path, opts);
    if (resp.status === 204) return null;
    const data = await resp.json();
    if (!resp.ok) {
        const msg = data?.error?.message || data?.detail?.[0]?.msg || JSON.stringify(data);
        throw new Error(msg);
    }
    return data;
}

export const api = {
    // Settings
    getSettings: () => request('GET', '/settings'),
    updateSettings: (data) => request('PUT', '/settings', data),

    // Voices
    listVoices: (lang) => request('GET', `/voices?lang=${encodeURIComponent(lang)}`),

    // Categories
    listCategories: () => request('GET', '/categories'),
    createCategory: (name) => request('POST', '/categories', { name }),
    updateCategory: (id, name) => request('PATCH', `/categories/${id}`, { name }),
    deleteCategory: (id) => request('DELETE', `/categories/${id}`),

    // Items
    listItems: (params = {}) => {
        const qs = new URLSearchParams();
        if (params.q) qs.set('q', params.q);
        if (params.category_id) qs.set('category_id', params.category_id);
        if (params.limit) qs.set('limit', params.limit);
        if (params.offset) qs.set('offset', params.offset);
        return request('GET', `/items?${qs}`);
    },
    createItem: (data) => request('POST', '/items', data),
    getItem: (id) => request('GET', `/items/${id}`),
    updateItem: (id, data) => request('PATCH', `/items/${id}`, data),
    deleteItem: (id) => request('DELETE', `/items/${id}`),
    regenerateAudio: (id) => request('POST', `/items/${id}/regenerate-audio`),

    // Practice
    practice: async (id, audioBlob) => {
        const form = new FormData();
        form.append('audio', audioBlob, 'recording.webm');
        return request('POST', `/items/${id}/practice`, form);
    },

    // Health
    healthProviders: () => request('GET', '/health/providers'),

    // Audio URL helper (not an API call)
    audioUrl: (id) => `${BASE}/items/${id}/audio`,
    audioDownloadUrl: (id) => `${BASE}/items/${id}/audio?download=1`,
};
