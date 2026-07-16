# Premium theme config for corporate LPR application
class Theme:
    # Font Settings
    FONT_FAMILY = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"

    # Dark Mode Palette (Zinc/Slate layered surfaces)
    BG_DEFAULT = "#090a0f"      # True dark layout background
    BG_SURFACE = "#12131a"      # Primary surface card background
    BG_SIDEBAR = "#0c0d14"      # Sidebar container
    BORDER_COLOR = "#1f222f"    # Low opacity subtle borders
    
    # Brand/Accent colors
    ACCENT = "#4f46e5"          # Indigo corporate brand accent
    ACCENT_LIGHT = "rgba(79, 70, 229, 0.1)"
    
    # Status indicators soft style
    COLOR_SUCCESS_BG = "rgba(16, 185, 129, 0.1)"
    COLOR_SUCCESS_FG = "#10b981"
    
    # Warning (Pending status)
    COLOR_WARNING_BG = "rgba(245, 158, 11, 0.1)"
    COLOR_WARNING_FG = "#f59e0b"
    
    # Danger (Unauthorized status)
    COLOR_DANGER_BG = "rgba(239, 68, 68, 0.1)"
    COLOR_DANGER_FG = "#ef4444"

    # Neutral / Offline status
    COLOR_MUTED_BG = "rgba(107, 114, 128, 0.1)"
    COLOR_MUTED_FG = "#9ca3af"
