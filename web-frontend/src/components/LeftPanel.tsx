import { CheckCircle2, Clock, Plus } from "lucide-react";
import { useTranslation } from "react-i18next";

import type { ComplaintSummary } from "../lib/types";

interface Props {
  complaints: ComplaintSummary[];
  activeId?: string;
  onSelect: (id: string) => void;
  onNew: () => void;
}

export function LeftPanel({ complaints, activeId, onSelect, onNew }: Props) {
  const { t } = useTranslation();

  return (
    <aside className="h-full flex flex-col bg-white border-r border-gray-200 overflow-hidden">
      <div className="px-3 py-3 border-b border-gray-200">
        <h2 className="text-sm font-bold uppercase text-gray-600 tracking-wide">
          {t("leftPanel.title")}
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {complaints.length === 0 && (
          <div className="text-xs text-gray-500 p-3 text-center">
            {t("leftPanel.noComplaints")}
          </div>
        )}

        {complaints.map((c) => (
          <button
            key={c.complaint_id}
            onClick={() => onSelect(c.complaint_id)}
            className={`w-full text-left p-3 rounded-lg border transition-colors ${
              c.complaint_id === activeId
                ? "bg-saffron/10 border-saffron"
                : "bg-gray-50 border-gray-200 hover:bg-gray-100"
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              {c.status === "resolved" ? (
                <CheckCircle2 size={14} className="text-govgreen" />
              ) : (
                <Clock size={14} className="text-saffron" />
              )}
              <span className="text-xs font-semibold text-gray-700">
                {c.department || t(`leftPanel.${c.status}`)}
              </span>
            </div>
            <p className="text-xs text-gray-600 line-clamp-2">{c.summary}</p>
          </button>
        ))}
      </div>

      <button
        onClick={onNew}
        className="m-2 py-3 px-3 bg-saffron text-white rounded-lg flex items-center justify-center gap-2 font-semibold hover:bg-saffron/90 transition-colors"
      >
        <Plus size={18} />
        <span className="text-sm">{t("leftPanel.newComplaint")}</span>
      </button>
    </aside>
  );
}
