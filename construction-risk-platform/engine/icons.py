"""Inline SVG icons for templates (no external icon fonts needed)."""
from markupsafe import Markup

_PATHS = {
    "gauge": '<polyline points="3 13 8.5 7.5 12.5 11 17 5"/><path d="M17 5h3v3"/><path d="M3 3v16a2 2 0 0 0 2 2h16"/>',
    "helmet": '<path d="M2 18h20"/><path d="M4 18v-4a8 8 0 0 1 16 0v4"/><path d="M9 6.2V10M15 6.2V10M9 10h6"/>',
    "clipboard": '<rect x="5" y="4" width="14" height="18" rx="2"/><path d="M9 4a2 2 0 0 1 6 0"/><path d="M9 11h6M9 15h4"/>',
    "shield": '<path d="M12 2l8 3.5V11c0 5-3.4 8.6-8 11-4.6-2.4-8-6-8-11V5.5z"/><path d="M8.5 11.5l2.5 2.5 4.5-4.5"/>',
    "doc": '<path d="M6 2h9l5 5v15H6z"/><path d="M14 2v6h6"/><path d="M9 13h6M9 17h6"/>',
    "cpu": '<rect x="5" y="5" width="14" height="14" rx="2"/><rect x="9.5" y="9.5" width="5" height="5" rx="1"/><path d="M9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3"/>',
    "site": '<path d="M3 21h18"/><path d="M5 21V5a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v16"/><path d="M15 9h3a2 2 0 0 1 2 2v10"/><path d="M8 7h3M8 11h3M8 15h3"/>',
    "bell": '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 0 1-3.4 0"/>',
    "alert": '<path d="M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/>',
    "menu": '<path d="M3 12h18M3 6h18M3 18h18"/>',
    "x": '<path d="M18 6L6 18M6 6l12 12"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "refresh": '<path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.5 9a9 9 0 0 1 14.9-3.4L23 10M1 14l4.6 4.4A9 9 0 0 0 20.5 15"/>',
    "play": '<path d="M6 4l14 8-14 8z"/>',
    "arrow": '<path d="M5 12h14M12 5l7 7-7 7"/>',
    "print": '<path d="M6 9V2h12v7"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/>',
}


def _make(p):
    def fn():
        return Markup(f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" style="width:18px;height:18px">{p}</svg>')
    return fn


icons = {k: _make(p) for k, p in _PATHS.items()}
