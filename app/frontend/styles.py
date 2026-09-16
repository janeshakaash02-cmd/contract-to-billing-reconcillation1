def get_custom_css() -> str:
    """
    Returns custom CSS for a blackish cyberpunk / fintech command center
    with electric neon green accents, glowing HUD cards, and high-contrast styling.
    """
    return """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

        /* Global Dark Terminal Base */
        :root {
            --bg-obsidian: #070A0F;
            --bg-card: #0D131F;
            --bg-card-hover: #121A2B;
            --bg-inset: #05070B;
            --neon-green: #00FF88;
            --neon-green-glow: rgba(0, 255, 136, 0.35);
            --neon-green-subtle: rgba(0, 255, 136, 0.12);
            --neon-cyan: #00F0FF;
            --neon-cyan-glow: rgba(0, 240, 255, 0.35);
            --neon-amber: #FFB800;
            --neon-crimson: #FF3366;
            --neon-purple: #B026FF;
            --text-primary: #F0F6FC;
            --text-secondary: #8B949E;
            --border-dim: #1E293B;
            --border-neon: rgba(0, 255, 136, 0.3);
        }

        html, body, [class*="css"], .stApp {
            font-family: 'Space Grotesk', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
            background-color: var(--bg-obsidian) !important;
            color: var(--text-primary) !important;
        }

        /* Top Header Glow Bar */
        header[data-testid="stHeader"] {
            background: rgba(7, 10, 15, 0.85) !important;
            backdrop-filter: blur(10px) !important;
            border-bottom: 1px solid rgba(0, 255, 136, 0.15) !important;
        }

        /* Sidebar Styling & Single-Line Sleek Navigation */
        section[data-testid="stSidebar"] {
            background-color: #05070B !important;
            border-right: 1px solid rgba(0, 255, 136, 0.18) !important;
            min-width: 290px !important;
        }
        section[data-testid="stSidebar"] hr {
            border-color: rgba(0, 255, 136, 0.15) !important;
        }
        
        /* Ensure Sidebar Radio Items Are Single-Line, Sleek & Modern */
        div[data-testid="stSidebar"] div[role="radiogroup"] {
            gap: 2px !important;
        }
        div[data-testid="stSidebar"] div[role="radiogroup"] label {
            white-space: nowrap !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            padding: 8px 12px !important;
            border-radius: 8px !important;
            transition: all 0.2s ease !important;
            border: 1px solid transparent !important;
            background: rgba(13, 19, 31, 0.4) !important;
            margin-bottom: 4px !important;
            cursor: pointer !important;
        }
        div[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
            background: rgba(0, 255, 136, 0.08) !important;
            border-color: rgba(0, 255, 136, 0.3) !important;
            transform: translateX(3px) !important;
        }
        div[data-testid="stSidebar"] div[role="radiogroup"] label p {
            white-space: nowrap !important;
            font-family: 'Space Grotesk', sans-serif !important;
            font-size: 0.88rem !important;
            font-weight: 500 !important;
            letter-spacing: 0.01em !important;
            line-height: 1.2 !important;
        }
        div[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
            background: rgba(0, 255, 136, 0.12) !important;
            border: 1px solid rgba(0, 255, 136, 0.45) !important;
            box-shadow: 0 0 14px rgba(0, 255, 136, 0.2) !important;
        }
        div[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {
            color: #00FF88 !important;
            font-weight: 600 !important;
            text-shadow: 0 0 8px rgba(0, 255, 136, 0.4) !important;
        }

        /* Pulsing Live Dot Animation */
        @keyframes neon-pulse {
            0% {
                box-shadow: 0 0 0 0 rgba(0, 255, 136, 0.7);
            }
            70% {
                box-shadow: 0 0 0 8px rgba(0, 255, 136, 0);
            }
            100% {
                box-shadow: 0 0 0 0 rgba(0, 255, 136, 0);
            }
        }
        .live-indicator {
            display: inline-block;
            width: 9px;
            height: 9px;
            border-radius: 50%;
            background-color: var(--neon-green);
            animation: neon-pulse 1.8s infinite;
            margin-right: 8px;
            vertical-align: middle;
        }

        /* Cyber HUD Banner */
        .cyber-banner {
            background: linear-gradient(135deg, rgba(0, 255, 136, 0.08) 0%, rgba(13, 19, 31, 0.95) 100%);
            border: 1px solid var(--border-neon);
            border-left: 5px solid var(--neon-green);
            border-radius: 10px;
            padding: 16px 22px;
            margin-bottom: 24px;
            box-shadow: 0 4px 20px rgba(0, 255, 136, 0.08);
            position: relative;
            overflow: hidden;
        }
        .cyber-banner::after {
            content: "SYSTEM ACTIVE // 256-BIT AUDIT";
            position: absolute;
            right: 15px;
            top: 10px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.65rem;
            color: var(--neon-green);
            letter-spacing: 0.12em;
            opacity: 0.6;
        }

        /* Neon Metric HUD Card */
        .metric-card {
            background: linear-gradient(145deg, #0C121F 0%, #070B13 100%);
            border: 1px solid rgba(0, 255, 136, 0.22);
            border-radius: 12px;
            padding: 18px 20px;
            box-shadow: 0 4px 18px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.04);
            color: #F8FAFC;
            margin-bottom: 14px;
            transition: all 0.25s ease-in-out;
            position: relative;
        }
        .metric-card:hover {
            border-color: var(--neon-green);
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.2), inset 0 1px 0 rgba(0, 255, 136, 0.2);
            transform: translateY(-2px);
        }
        .metric-card-danger {
            border-color: rgba(255, 51, 102, 0.4);
        }
        .metric-card-danger:hover {
            border-color: var(--neon-crimson);
            box-shadow: 0 0 20px rgba(255, 51, 102, 0.25);
        }
        .metric-card-cyan {
            border-color: rgba(0, 240, 255, 0.35);
        }
        .metric-card-cyan:hover {
            border-color: var(--neon-cyan);
            box-shadow: 0 0 20px rgba(0, 240, 255, 0.25);
        }
        .metric-label {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.74rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #8B949E;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .metric-value {
            font-family: 'Space Grotesk', sans-serif;
            font-size: 2rem;
            font-weight: 700;
            color: #FFFFFF;
            letter-spacing: -0.02em;
            line-height: 1.1;
        }
        .metric-value-green {
            color: var(--neon-green);
            text-shadow: 0 0 14px rgba(0, 255, 136, 0.35);
        }
        .metric-value-crimson {
            color: var(--neon-crimson);
            text-shadow: 0 0 14px rgba(255, 51, 102, 0.35);
        }
        .metric-value-cyan {
            color: var(--neon-cyan);
            text-shadow: 0 0 14px rgba(0, 240, 255, 0.35);
        }
        .metric-sub {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            color: var(--neon-green);
            margin-top: 6px;
            display: flex;
            align-items: center;
            gap: 4px;
        }

        /* Neon Status Badges */
        .badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 6px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.74rem;
            font-weight: 600;
            letter-spacing: 0.04em;
            text-align: center;
            text-transform: uppercase;
        }
        .badge-matched {
            background-color: rgba(0, 255, 136, 0.12);
            color: var(--neon-green);
            border: 1px solid rgba(0, 255, 136, 0.4);
            box-shadow: 0 0 10px rgba(0, 255, 136, 0.15);
        }
        .badge-probable {
            background-color: rgba(0, 240, 255, 0.12);
            color: var(--neon-cyan);
            border: 1px solid rgba(0, 240, 255, 0.4);
            box-shadow: 0 0 10px rgba(0, 240, 255, 0.15);
        }
        .badge-unmatched {
            background-color: rgba(255, 51, 102, 0.12);
            color: var(--neon-crimson);
            border: 1px solid rgba(255, 51, 102, 0.4);
            box-shadow: 0 0 10px rgba(255, 51, 102, 0.15);
        }
        .badge-duplicate {
            background-color: rgba(255, 184, 0, 0.12);
            color: var(--neon-amber);
            border: 1px solid rgba(255, 184, 0, 0.4);
        }
        .badge-dq {
            background-color: rgba(176, 38, 255, 0.12);
            color: var(--neon-purple);
            border: 1px solid rgba(176, 38, 255, 0.4);
        }

        /* Visual Diff Inspector Cards */
        .diff-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin: 16px 0;
        }
        .diff-card {
            background: #0B101A;
            border: 1px solid #1E293B;
            border-radius: 10px;
            padding: 16px;
            position: relative;
        }
        .diff-card-contract {
            border-top: 3px solid var(--neon-cyan);
        }
        .diff-card-invoice {
            border-top: 3px solid var(--neon-green);
        }
        .diff-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 0.88rem;
        }
        .diff-row:last-child {
            border-bottom: none;
        }
        .diff-row-mismatch {
            background-color: rgba(255, 51, 102, 0.09);
            border-left: 3px solid var(--neon-crimson);
            padding-left: 8px;
            border-radius: 4px;
        }
        .diff-row-match {
            background-color: rgba(0, 255, 136, 0.05);
            border-left: 3px solid var(--neon-green);
            padding-left: 8px;
            border-radius: 4px;
        }

        /* Cyber Terminal Simulation Box */
        .terminal-box {
            background-color: #04060A;
            border: 1px solid rgba(0, 255, 136, 0.3);
            border-radius: 8px;
            padding: 14px 18px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            color: #A3E635;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.6), inset 0 0 15px rgba(0, 255, 136, 0.04);
            line-height: 1.6;
            max-height: 280px;
            overflow-y: auto;
            margin: 14px 0;
        }
        .terminal-box .term-green {
            color: #00FF88;
        }
        .terminal-box .term-dim {
            color: #4B5563;
        }
        .terminal-box .term-cyan {
            color: #00F0FF;
        }
        .terminal-box .term-red {
            color: #FF3366;
        }

        /* AI Analysis Card */
        .analysis-box {
            background: linear-gradient(145deg, #0A0F1A 0%, #060910 100%);
            border: 1px solid rgba(0, 240, 255, 0.25);
            border-left: 5px solid var(--neon-cyan);
            border-radius: 8px;
            padding: 18px 20px;
            margin: 14px 0;
            color: #E2E8F0;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
        }
        .analysis-box h4 {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.82rem;
            letter-spacing: 0.05em;
            color: var(--neon-cyan);
            margin-top: 14px;
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .analysis-box h4:first-child {
            margin-top: 0;
        }
        .analysis-box p {
            font-size: 0.9rem;
            color: #CBD5E1;
            line-height: 1.5;
            margin-bottom: 10px;
        }

        /* Citation Tag */
        .citation-tag {
            background-color: rgba(0, 240, 255, 0.1);
            border: 1px solid rgba(0, 240, 255, 0.35);
            border-radius: 4px;
            padding: 3px 8px;
            font-size: 0.74rem;
            font-family: 'JetBrains Mono', monospace;
            color: var(--neon-cyan);
            display: inline-block;
            margin: 2px 4px 2px 0;
        }

        /* Streamlit Button Customization */
        div.stButton > button {
            background: linear-gradient(180deg, #0E1829 0%, #080E18 100%) !important;
            border: 1px solid rgba(0, 255, 136, 0.35) !important;
            color: var(--neon-green) !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            transition: all 0.2s ease-in-out !important;
            text-transform: uppercase !important;
            letter-spacing: 0.04em !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4) !important;
        }
        div.stButton > button:hover {
            border-color: var(--neon-green) !important;
            box-shadow: 0 0 15px rgba(0, 255, 136, 0.4) !important;
            color: #FFFFFF !important;
            background: rgba(0, 255, 136, 0.15) !important;
            transform: translateY(-1px) !important;
        }
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #00FF88 0%, #00CC6A 100%) !important;
            color: #000000 !important;
            font-weight: 700 !important;
            border: none !important;
            box-shadow: 0 0 18px rgba(0, 255, 136, 0.45) !important;
        }
        div.stButton > button[kind="primary"]:hover {
            box-shadow: 0 0 26px rgba(0, 255, 136, 0.7) !important;
            transform: scale(1.02) !important;
        }

        /* Tabs Styling */
        button[data-baseweb="tab"] {
            background: transparent !important;
            border: none !important;
            color: #8B949E !important;
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 0.85rem !important;
            font-weight: 500 !important;
            padding: 10px 18px !important;
            transition: all 0.2s ease !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: var(--neon-green) !important;
            border-bottom: 2px solid var(--neon-green) !important;
            text-shadow: 0 0 10px rgba(0, 255, 136, 0.4) !important;
        }

        /* Form & Input Enhancements */
        div[data-baseweb="input"], div[data-baseweb="select"] {
            background-color: #0B101A !important;
            border-color: rgba(0, 255, 136, 0.2) !important;
            border-radius: 8px !important;
        }
        div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within {
            border-color: var(--neon-green) !important;
            box-shadow: 0 0 12px rgba(0, 255, 136, 0.25) !important;
        }

        /* Dataframe Enhancements */
        div[data-testid="stDataFrame"] {
            background-color: #0A0E17 !important;
            border: 1px solid rgba(0, 255, 136, 0.15) !important;
            border-radius: 10px !important;
            overflow: hidden !important;
        }

        /* Slider Neon Accent */
        div[data-testid="stSlider"] div[role="slider"] {
            background-color: var(--neon-green) !important;
            box-shadow: 0 0 10px rgba(0, 255, 136, 0.6) !important;
        }
    </style>
    """
