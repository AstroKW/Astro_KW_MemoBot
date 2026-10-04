import os
import json

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "user_settings.json")

PRESETS = {
    "Astro Dark (Predefinito)": {
        "bg_color": "#0d1117",
        "secondary_bg_color": "#161b22",
        "sidebar_bg_color": "#090d13",
        "text_color": "#f0f6fc",
        "accent_color": "#ff4b4b",
        "border_color": "#30363d",
        "font_family": "Inter",
        "font_size": "Normale (100%)",
        "density": "Standard",
        "high_contrast_focus": True
    },
    "Carta & Inchiostro (Sepia / Chiaro)": {
        "bg_color": "#fdfbf7",
        "secondary_bg_color": "#f4ede2",
        "sidebar_bg_color": "#ebe2d5",
        "text_color": "#24211d",
        "accent_color": "#b84a39",
        "border_color": "#d8cfc4",
        "font_family": "Inter",
        "font_size": "Normale (100%)",
        "density": "Standard",
        "high_contrast_focus": True
    },
    "Alto Contrasto (WCAG AAA - Ipovisione)": {
        "bg_color": "#000000",
        "secondary_bg_color": "#121212",
        "sidebar_bg_color": "#000000",
        "text_color": "#ffffff",
        "accent_color": "#ffff00",
        "border_color": "#ffff00",
        "font_family": "Atkinson Hyperlegible",
        "font_size": "Grande (120%)",
        "density": "Spaziosa",
        "high_contrast_focus": True
    },
    "Nordic Frost (Ardesia & Ciano)": {
        "bg_color": "#0f172a",
        "secondary_bg_color": "#1e293b",
        "sidebar_bg_color": "#0b1120",
        "text_color": "#f8fafc",
        "accent_color": "#06b6d4",
        "border_color": "#334155",
        "font_family": "Lexend",
        "font_size": "Normale (100%)",
        "density": "Standard",
        "high_contrast_focus": True
    }
}

DEFAULT_SETTINGS = {
    "preset": "Astro Dark (Predefinito)",
    **PRESETS["Astro Dark (Predefinito)"]
}

def carica_impostazioni() -> dict:
    """Carica le impostazioni da user_settings.json o crea quelle predefinite."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Unisci con i valori predefiniti per garantire completezza
                settings = DEFAULT_SETTINGS.copy()
                settings.update(data)
                return settings
        except Exception as e:
            print(f"[SETTINGS] Errore lettura {SETTINGS_FILE}: {e}")
    return DEFAULT_SETTINGS.copy()

def salva_impostazioni(settings: dict) -> bool:
    """Salva le impostazioni nel file user_settings.json."""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[SETTINGS] Errore salvataggio {SETTINGS_FILE}: {e}")
        return False

def genera_css_accessibilita(settings: dict) -> str:
    """
    Genera le regole CSS per iniettare i colori, la tipografia,
    la dimensione dei font e gli stili di accessibilità (WCAG).
    """
    bg = settings.get("bg_color", "#0d1117")
    sec_bg = settings.get("secondary_bg_color", "#161b22")
    side_bg = settings.get("sidebar_bg_color", "#090d13")
    txt = settings.get("text_color", "#f0f6fc")
    acc = settings.get("accent_color", "#ff4b4b")
    border = settings.get("border_color", "#30363d")
    family = settings.get("font_family", "Inter")
    size_str = settings.get("font_size", "Normale (100%)")
    density = settings.get("density", "Standard")
    high_contrast = settings.get("high_contrast_focus", True)

    # Mappatura dimensione font
    size_map = {
        "Compatta (90%)": "0.92rem",
        "Normale (100%)": "1.05rem",
        "Grande (120%)": "1.25rem",
        "Molto Grande (140%)": "1.45rem"
    }
    font_size_val = size_map.get(size_str, "1.05rem")

    # Mappatura spaziatura densità
    padding_card = "8px 14px" if density == "Compatta" else ("16px 22px" if density == "Spaziosa" else "12px 18px")
    margin_card = "4px 0" if density == "Compatta" else ("12px 0" if density == "Spaziosa" else "8px 0")

    # Regole per il focus della tastiera (accessibilità motoria/visiva)
    focus_rule = f"""
    *:focus-visible {{
        outline: 3px solid {acc} !important;
        outline-offset: 2px !important;
    }}
    """ if high_contrast else ""

    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400&family=Inter:wght@400;500;600;700&family=Lexend:wght@400;500;600;700&display=swap');

    /* Variabili native di Streamlit per forzare il tema in tutto il framework */
    :root, [data-testid="stAppViewContainer"], .stApp {{
        --text-color: {txt} !important;
        --background-color: {bg} !important;
        --secondary-background-color: {sec_bg} !important;
        --primary-color: {acc} !important;
    }}

    html, body, [class*="css"], .stApp, 
    .stApp p, .stApp span, .stApp label, 
    .stApp div[data-testid="stMarkdownContainer"] *,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
    .stApp div[data-testid="stCaptionContainer"] *,
    .stApp details summary, .stApp details summary *,
    .stApp .stMarkdown, .stApp .stMarkdown * {{
        font-family: '{family}', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        color: {txt} !important;
    }}

    /* Preserva i font nativi per le icone di sistema ed expander Streamlit (evita la scritta 'keyboard_arrow_right') */
    [data-testid="stExpanderToggleIcon"],
    [data-testid="stIconMaterial"],
    .material-symbols-rounded,
    .material-symbols-outlined,
    .material-icons,
    details summary span[translate="no"] {{
        font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons" !important;
        font-weight: normal !important;
        font-style: normal !important;
        display: inline-block !important;
        line-height: 1 !important;
        white-space: nowrap !important;
    }}

    .stApp {{
        font-size: {font_size_val} !important;
        background-color: {bg} !important;
    }}

    /* Barra Laterale (Sidebar) */
    section[data-testid="stSidebar"] {{
        background-color: {side_bg} !important;
        border-right: 1px solid {border} !important;
    }}
    
    section[data-testid="stSidebar"] * {{
        color: {txt} !important;
    }}

    /* Header superiore Streamlit */
    header[data-testid="stHeader"] {{
        background-color: {bg} !important;
    }}

    /* Expander dei Memo e Sidebar */
    div[data-testid="stExpander"] {{
        background-color: {sec_bg} !important;
        border: 1px solid {border} !important;
        border-radius: 8px !important;
        margin: {margin_card} !important;
        transition: all 0.2s ease-in-out !important;
    }}
    
    div[data-testid="stExpander"]:hover {{
        border-color: {acc} !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    }}

    div[data-testid="stExpander"] details,
    div[data-testid="stExpander"] details summary,
    div[data-testid="stExpander"] details[open] summary {{
        background-color: {sec_bg} !important;
        padding: {padding_card} !important;
        color: {txt} !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
    }}

    div[data-testid="stExpander"] details summary:hover {{
        background-color: {sec_bg} !important;
        color: {acc} !important;
    }}

    div[data-testid="stExpander"] details[open] summary {{
        border-bottom: 1px solid {border} !important;
        border-bottom-left-radius: 0 !important;
        border-bottom-right-radius: 0 !important;
    }}

    div[data-testid="stExpander"] details div[data-testid="stExpanderDetails"] {{
        background-color: {sec_bg} !important;
        color: {txt} !important;
        border-radius: 0 0 8px 8px !important;
    }}

    div[data-testid="stExpander"] details summary svg {{
        fill: {txt} !important;
    }}

    /* Schede di navigazione (Tabs) con Wrapping Responsivo (non spariscono più a destra) */
    div[data-baseweb="tab-list"] {{
        flex-wrap: wrap !important;
        gap: 4px 6px !important;
        overflow-x: visible !important;
        white-space: normal !important;
    }}

    button[data-baseweb="tab"] {{
        font-size: calc({font_size_val} * 0.92) !important;
        color: {txt} !important;
        padding: 6px 12px !important;
        border-radius: 6px !important;
        margin-bottom: 4px !important;
        border-bottom: 2px solid transparent !important;
    }}

    button[data-baseweb="tab"] * {{
        color: {txt} !important;
    }}
    
    button[data-baseweb="tab"][aria-selected="true"] {{
        border-bottom-color: {acc} !important;
        color: {acc} !important;
        font-weight: 700 !important;
    }}

    button[data-baseweb="tab"][aria-selected="true"] * {{
        color: {acc} !important;
    }}

    /* Pulsanti Primari e Popover */
    button[kind="primary"], button[kind="primary"] * {{
        background-color: {acc} !important;
        border-color: {acc} !important;
        color: #ffffff !important;
        font-weight: 600 !important;
    }}

    /* Popover */
    div[data-testid="stPopoverBody"] {{
        background-color: {sec_bg} !important;
        border: 1px solid {border} !important;
        color: {txt} !important;
        border-radius: 8px !important;
    }}

    div[data-testid="stPopoverBody"] * {{
        color: {txt} !important;
    }}

    /* Blocchi di codice, trascrizioni e testo originale */
    div[data-testid="stText"],
    div[data-testid="stText"] *,
    div[data-testid="stText"] pre,
    code, pre {{
        background-color: {bg} !important;
        color: {txt} !important;
        border: 1px solid {border} !important;
        font-size: calc({font_size_val} * 0.92) !important;
    }}

    /* Checkbox coerenti col tema */
    div[data-baseweb="checkbox"] span {{
        background-color: {sec_bg} !important;
        border-color: {border} !important;
    }}

    /* Campi di input e textarea */
    input, textarea, [data-baseweb="base-input"], [data-baseweb="base-input"] * {{
        background-color: {sec_bg} !important;
        color: {txt} !important;
        border-color: {border} !important;
    }}
    
    /* Dropdown / Selectbox */
    div[data-baseweb="select"] > div {{
        background-color: {sec_bg} !important;
        color: {txt} !important;
        border-color: {border} !important;
    }}

    div[data-baseweb="select"] * {{
        color: {txt} !important;
    }}

    /* Menu a discesa aperto */
    ul[data-testid="stSelectboxMenu"], ul[data-testid="stSelectboxMenu"] * {{
        background-color: {sec_bg} !important;
        color: {txt} !important;
    }}

    /* Pulsanti secondari */
    button[kind="secondary"], button[kind="secondary"] * {{
        background-color: {sec_bg} !important;
        color: {txt} !important;
        border-color: {border} !important;
    }}
    button[kind="secondary"]:hover, button[kind="secondary"]:hover * {{
        border-color: {acc} !important;
        color: {acc} !important;
    }}

    /* Link */
    a, a * {{
        color: {acc} !important;
    }}

    /* Indicatore Focus da tastiera per ausili e accessibilità */
    {focus_rule}

    /* Riquadri informativi */
    div[data-testid="stAlert"] {{
        background-color: {sec_bg} !important;
        border-left: 4px solid {acc} !important;
        color: {txt} !important;
    }}

    div[data-testid="stAlert"] * {{
        color: {txt} !important;
    }}
    </style>
    """
    return css
