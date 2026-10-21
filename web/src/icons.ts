const paths: Record<string,string> = {
 check: '<path d="m5 12 4 4L19 6"/>',
 x: '<path d="m6 6 12 12M18 6 6 18"/>',
 sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/>',
 moon: '<path d="M20.5 14A9 9 0 0 1 10 3.5 9 9 0 1 0 20.5 14Z"/>',
 copy: '<rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V3H3v13h5"/>',
 edit: '<path d="m15 4 5 5M4 20l5-1L21 7l-5-5L4 14z"/>',
 up: '<path d="m6 15 6-6 6 6"/>', down: '<path d="m6 9 6 6 6-6"/>',
 panel: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16m6-11-3 3 3 3"/>',
 filter: '<path d="M4 7h16M7 12h10M10 17h4"/><circle cx="8" cy="7" r="2"/><circle cx="16" cy="12" r="2"/>',
 search: '<circle cx="10" cy="10" r="6"/><path d="m15 15 5 5"/>',
};
export const icon = (name: string): string => `<svg class="icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] ?? paths.panel}</svg>`;
