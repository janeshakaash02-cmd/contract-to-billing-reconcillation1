def get_custom_css() -> str:
    return """
    <style>
        /* Modern Finance Theme */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        /* Metric Card Styling */
        .metric-card {
            background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 18px 20px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            color: #F8FAFC;
            margin-bottom: 12px;
        }
        .metric-label {
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #94A3B8;
            margin-bottom: 6px;
            font-weight: 500;
        }
        .metric-value {
            font-size: 1.85rem;
            font-weight: 700;
            color: #FFFFFF;
            letter-spacing: -0.02em;
        }
        .metric-sub {
            font-size: 0.78rem;
            color: #10B981;
            margin-top: 4px;
        }
        
        /* Status Badges */
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.02em;
            text-align: center;
        }
        .badge-matched {
            background-color: rgba(16, 185, 129, 0.15);
            color: #10B981;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        .badge-probable {
            background-color: rgba(59, 130, 246, 0.15);
            color: #60A5FA;
            border: 1px solid rgba(59, 130, 246, 0.3);
        }
        .badge-unmatched {
            background-color: rgba(239, 68, 68, 0.15);
            color: #F87171;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }
        .badge-duplicate {
            background-color: rgba(245, 158, 11, 0.15);
            color: #FBBF24;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }
        .badge-dq {
            background-color: rgba(168, 85, 247, 0.15);
            color: #C084FC;
            border: 1px solid rgba(168, 85, 247, 0.3);
        }
        
        /* Priority Badges */
        .priority-high {
            background-color: #DC2626;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.72rem;
            font-weight: 700;
        }
        .priority-med {
            background-color: #D97706;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.72rem;
            font-weight: 700;
        }
        .priority-low {
            background-color: #059669;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.72rem;
            font-weight: 700;
        }
        
        /* Analysis Boxes */
        .analysis-box {
            background-color: #0F172A;
            border-left: 4px solid #3B82F6;
            border-radius: 4px 8px 8px 4px;
            padding: 14px 16px;
            margin: 10px 0;
            color: #E2E8F0;
        }
        .citation-tag {
            background-color: #1E293B;
            border: 1px solid #475569;
            border-radius: 6px;
            padding: 3px 8px;
            font-size: 0.75rem;
            font-family: monospace;
            color: #38BDF8;
            display: inline-block;
            margin: 2px 4px 2px 0;
        }
        
        /* Table enhancements */
        div[data-testid="stDataFrame"] {
            border-radius: 8px;
            overflow: hidden;
        }
    </style>
    """
