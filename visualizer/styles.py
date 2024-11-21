# Colors
COLORS = {
    "primary": "#138600",  # Material Blue 700
    "secondary": "#424242",  # Material Grey 800
    "white": "#FFFFFF",
    "text": "rgb(60, 60, 60)",
    "background": {"light": "#FFFFFF", "alternate": "#f5f5f5"},
}

# Typography
TYPOGRAPHY = {
    "fontFamily": "Roboto, sans-serif",
    "sizes": {"large": "34px", "medium": "24px", "small": "16px", "body": "14px"},
    "weights": {"regular": "400", "bold": "bold"},
}

# Spacing
SPACING = {"small": "8px", "medium": "16px", "large": "24px"}

# Table Styles
TABLE_STYLES = {
    "cell": {
        "textAlign": "center",
        "padding": SPACING["medium"],
        "fontFamily": TYPOGRAPHY["fontFamily"],
        "fontSize": TYPOGRAPHY["sizes"]["body"],
        "border": "none",
    },
    "header": {
        "textAlign": "center",
        "fontWeight": TYPOGRAPHY["weights"]["bold"],
        "backgroundColor": COLORS["primary"],
        "color": COLORS["white"],
        "fontSize": TYPOGRAPHY["sizes"]["small"],
        "border": "none",
        "padding": SPACING["medium"],
    },
    "data": {"backgroundColor": COLORS["background"]["light"], "color": COLORS["text"]},
    "data_conditional": [
        {
            "if": {"row_index": "odd"},
            "backgroundColor": COLORS["background"]["alternate"],
        }
    ],
    "table": {
        "margin": SPACING["large"],
        "borderRadius": "4px",
        "overflow": "hidden",
        "boxShadow": "0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)",
        "border": "none",
    },
}

# Header Styles
HEADER_1 = {
    "color": COLORS["primary"],
    "fontFamily": TYPOGRAPHY["fontFamily"],
    "fontSize": TYPOGRAPHY["sizes"]["large"],
    "fontWeight": TYPOGRAPHY["weights"]["regular"],
    "letterSpacing": "-0.01562em",
    "marginBottom": SPACING["large"],
    "marginTop": SPACING["large"],
    "padding": f'0 {SPACING["large"]}',
}

HEADER_2 = (
    {
        "color": COLORS["secondary"],
        "fontFamily": TYPOGRAPHY["fontFamily"],
        "fontSize": TYPOGRAPHY["sizes"]["medium"],
        "fontWeight": TYPOGRAPHY["weights"]["regular"],
        "letterSpacing": "0em",
        "marginBottom": SPACING["medium"],
        "marginTop": SPACING["large"],
        "padding": f'0 {SPACING["large"]}',
    },
)
CONTAINER = {"maxWidth": "1200px", "margin": "0 auto", "padding": SPACING["large"]}
LINE_COLORS = [
    COLORS["primary"],  # Primary green
    "#1976D2",  # Blue
    "#E53935",  # Red
    "#7B1FA2",  # Purple
    "#FF8F00",  # Amber
    "#00897B",  # Teal
    "#C62828",  # Dark Red
    "#3949AB",  # Indigo
    "#2E7D32",  # Dark Green
    "#6D4C41",  # Brown
]
