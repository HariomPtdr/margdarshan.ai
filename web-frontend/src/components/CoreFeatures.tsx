/**
 * CoreFeatures — Marketing section for Shikayat Saathi login page.
 * Three gradient cards showcasing key capabilities.
 * Static only — no animations, no JS behavior.
 */

export function CoreFeatures() {
  return (
    <div className="c1-container">
      {/* Header */}
      <div className="c1-header">
        <div className="c1-badge">SHIKAYAT SAATHI</div>
        <h1 className="c1-title">Built for Every Citizen</h1>
        <p className="c1-subtitle">
          File government complaints in seconds
          <br />
          in Hindi, English, or Hinglish
        </p>
      </div>

      {/* Grid */}
      <div className="c1-grid">

        {/* Card 1 — AI Guided Complaint */}
        <div className="c1-card c1-card-1">
          {/* Simulated chat bubble */}
          <div className="c1-prompt-box">
            <div className="c1-chat-msg c1-chat-user">bijli nahi aa rahi 3 din se</div>
            <div className="c1-chat-msg c1-chat-bot">
              Samajh gaya —{" "}
              <span className="c1-blur-text">bijli problem</span>
              . Kya sirf aapke ghar mein hai ya{" "}
              <span className="c1-blur-text">poore area</span> mein?
            </div>
          </div>
          {/* Language pill */}
          <div className="c1-lang-pill">
            <span className="c1-star">✦</span>
            Hindi · English · Hinglish
          </div>
          {/* Cursor */}
          <svg className="c1-cursor" viewBox="0 0 24 24" fill="#0f172a">
            <path d="M4 2L20 11L11 13L9 22L4 2Z" stroke="white" strokeWidth="1" />
          </svg>
          <h3>AI Guided Complaint Filing</h3>
        </div>

        {/* Card 2 — Smart Routing */}
        <div className="c1-card c1-card-2">
          <div className="c1-routing-visual">
            {/* Central hub */}
            <div className="c1-hub">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" strokeWidth="2" strokeLinecap="round">
                <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
                <polyline points="9 22 9 12 15 12 15 22" />
              </svg>
              <span>Your Complaint</span>
            </div>
            {/* Connectors */}
            <div className="c1-portals">
              {[
                { name: "CPGRAMS", color: "#f59e0b" },
                { name: "MP CM 181", color: "#8b5cf6" },
                { name: "MPPKVVCL", color: "#3b82f6" },
                { name: "IMC Portal", color: "#10b981" },
                { name: "Police Portal", color: "#ef4444" },
                { name: "+65 more", color: "#6b7280" },
              ].map((p) => (
                <div key={p.name} className="c1-portal-chip" style={{ borderColor: p.color + "40", background: p.color + "15" }}>
                  <span className="c1-portal-dot" style={{ background: p.color }} />
                  {p.name}
                </div>
              ))}
            </div>
          </div>
          <h3>Smart Portal Routing</h3>
        </div>

        {/* Card 3 — Track & Review */}
        <div className="c1-card c1-card-3">
          {/* Mesh overlay */}
          <div className="c1-mesh" />
          {/* Status card */}
          <div className="c1-status-card">
            <div className="c1-status-header">
              <div className="c1-status-dot c1-dot-green" />
              <span className="c1-status-label">Complaint Submitted</span>
            </div>
            <div className="c1-ticket-row">
              <span className="c1-ticket-label">Ticket</span>
              <span className="c1-ticket-id">ELE/4628119027</span>
            </div>
            <div className="c1-ticket-row">
              <span className="c1-ticket-label">Portal</span>
              <span className="c1-ticket-val">MPPKVVCL Indore</span>
            </div>
            <div className="c1-ticket-row">
              <span className="c1-ticket-label">Status</span>
              <span className="c1-ticket-status">Under Review</span>
            </div>
          </div>
          {/* Search pill */}
          <div className="c1-search">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
              stroke="#64748b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            Track your complaint
          </div>
          <h3>Real-Time Status Tracking</h3>
        </div>

      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

        .c1-container {
          max-width: 1100px;
          width: 100%;
          text-align: center;
          font-family: 'Inter', sans-serif;
        }

        .c1-header { margin-bottom: 0; }

        .c1-badge {
          font-size: 0.75rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 1px;
          background: linear-gradient(90deg, #F5C344, #F28482, #B567C2);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          margin-bottom: 14px;
          display: inline-block;
        }

        .c1-title {
          font-size: 2.5rem;
          font-weight: 500;
          color: #0f172a;
          letter-spacing: -0.02em;
          margin-bottom: 12px;
          font-family: 'Inter', sans-serif;
        }

        .c1-subtitle {
          font-size: 1.05rem;
          color: #64748b;
          line-height: 1.6;
          margin-bottom: 40px;
          font-family: 'Inter', sans-serif;
        }

        .c1-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 20px;
        }

        @media (max-width: 900px) {
          .c1-grid { grid-template-columns: repeat(2, 1fr); }
          .c1-title { font-size: 2rem; }
        }

        @media (max-width: 600px) {
          .c1-grid { grid-template-columns: 1fr; }
          .c1-title { font-size: 1.75rem; }
        }

        .c1-card {
          border-radius: 20px;
          height: 320px;
          display: flex;
          flex-direction: column;
          justify-content: flex-end;
          position: relative;
          overflow: hidden;
          text-align: left;
          box-shadow: 0 10px 30px -10px rgba(0,0,0,0.12);
        }

        .c1-card h3 {
          font-size: 1rem;
          font-weight: 600;
          color: #1e293b;
          padding: 20px 24px;
          z-index: 2;
          position: relative;
          font-family: 'Inter', sans-serif;
        }

        /* ── Card 1 ── */
        .c1-card-1 {
          background: radial-gradient(circle at 50% 0%, #FFB347 0%, #F9ED96 30%, #F4F8F9 60%, #F4F8F9 100%);
        }

        .c1-prompt-box {
          position: absolute;
          top: 24px;
          left: 20px;
          right: 20px;
          background: white;
          border-radius: 12px;
          padding: 14px;
          font-size: 0.78rem;
          color: #475569;
          line-height: 1.6;
          box-shadow: 0 8px 20px rgba(0,0,0,0.06);
          display: flex;
          flex-direction: column;
          gap: 8px;
          z-index: 2;
        }

        .c1-chat-msg {
          padding: 8px 12px;
          border-radius: 10px;
          font-size: 0.77rem;
          line-height: 1.5;
          font-family: 'Inter', sans-serif;
        }

        .c1-chat-user {
          background: #f1f5f9;
          color: #334155;
          align-self: flex-end;
          max-width: 85%;
        }

        .c1-chat-bot {
          background: #fffbeb;
          color: #475569;
          border: 1px solid #fde68a;
          align-self: flex-start;
          max-width: 100%;
        }

        .c1-blur-text {
          background: linear-gradient(90deg, #FFB347, #E5A1F5);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          font-weight: 600;
        }

        .c1-lang-pill {
          position: absolute;
          top: 218px;
          left: 36px;
          background: white;
          border: 1px solid #e2e8f0;
          padding: 5px 14px;
          border-radius: 20px;
          font-size: 0.72rem;
          font-weight: 600;
          color: #1e293b;
          box-shadow: 0 4px 15px rgba(0,0,0,0.08);
          display: flex;
          align-items: center;
          gap: 6px;
          z-index: 3;
          font-family: 'Inter', sans-serif;
        }

        .c1-star { color: #a855f7; font-size: 0.9rem; }

        .c1-cursor {
          position: absolute;
          top: 230px;
          left: 168px;
          width: 22px;
          height: 22px;
          filter: drop-shadow(0 4px 6px rgba(0,0,0,0.2));
          z-index: 10;
        }

        /* ── Card 2 ── */
        .c1-card-2 {
          background: radial-gradient(circle at 50% 0%, #E5A1F5 0%, #F8ACA0 30%, #F4F8F9 60%, #F4F8F9 100%);
        }

        .c1-routing-visual {
          position: absolute;
          top: 16px;
          left: 0;
          right: 0;
          bottom: 60px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 0 20px;
          gap: 12px;
          z-index: 2;
        }

        .c1-hub {
          background: white;
          border-radius: 12px;
          padding: 10px 18px;
          display: flex;
          align-items: center;
          gap: 8px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.08);
          font-size: 0.78rem;
          font-weight: 600;
          color: #1e293b;
          font-family: 'Inter', sans-serif;
        }

        .c1-portals {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          justify-content: center;
        }

        .c1-portal-chip {
          border: 1px solid;
          border-radius: 20px;
          padding: 3px 10px;
          font-size: 0.68rem;
          font-weight: 500;
          color: #334155;
          display: flex;
          align-items: center;
          gap: 5px;
          font-family: 'Inter', sans-serif;
        }

        .c1-portal-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          flex-shrink: 0;
        }

        /* ── Card 3 ── */
        .c1-card-3 {
          background: radial-gradient(circle at 50% 0%, #F9ED96 0%, #E5A1F5 30%, #F4F8F9 60%, #F4F8F9 100%);
        }

        .c1-mesh {
          position: absolute;
          inset: 0;
          background-image:
            linear-gradient(rgba(255,255,255,0.7) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.7) 1px, transparent 1px);
          background-size: 18px 18px;
          -webkit-mask-image: radial-gradient(circle at center top, black 0%, transparent 75%);
          mask-image: radial-gradient(circle at center top, black 0%, transparent 75%);
          z-index: 0;
        }

        .c1-status-card {
          position: absolute;
          top: 28px;
          left: 20px;
          right: 20px;
          background: white;
          border-radius: 14px;
          padding: 14px 16px;
          box-shadow: 0 8px 24px rgba(0,0,0,0.08);
          z-index: 2;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .c1-status-header {
          display: flex;
          align-items: center;
          gap: 8px;
          padding-bottom: 8px;
          border-bottom: 1px solid #f1f5f9;
        }

        .c1-status-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
        .c1-dot-green { background: #22c55e; box-shadow: 0 0 0 3px rgba(34,197,94,0.2); }

        .c1-status-label {
          font-size: 0.78rem;
          font-weight: 600;
          color: #1e293b;
          font-family: 'Inter', sans-serif;
        }

        .c1-ticket-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-family: 'Inter', sans-serif;
        }

        .c1-ticket-label {
          font-size: 0.7rem;
          color: #94a3b8;
          font-weight: 500;
        }

        .c1-ticket-id {
          font-size: 0.72rem;
          font-weight: 600;
          color: #3b82f6;
          font-family: monospace;
        }

        .c1-ticket-val {
          font-size: 0.72rem;
          font-weight: 500;
          color: #334155;
        }

        .c1-ticket-status {
          font-size: 0.68rem;
          font-weight: 600;
          color: #f59e0b;
          background: #fffbeb;
          border: 1px solid #fde68a;
          border-radius: 10px;
          padding: 2px 8px;
        }

        .c1-search {
          position: absolute;
          top: 226px;
          left: 50%;
          transform: translateX(-50%);
          background: white;
          border: 1px solid #e2e8f0;
          padding: 6px 18px;
          border-radius: 20px;
          font-size: 0.72rem;
          font-weight: 500;
          color: #1e293b;
          box-shadow: 0 8px 20px rgba(0,0,0,0.07);
          white-space: nowrap;
          display: flex;
          align-items: center;
          gap: 8px;
          z-index: 3;
          font-family: 'Inter', sans-serif;
        }
      `}</style>
    </div>
  );
}
