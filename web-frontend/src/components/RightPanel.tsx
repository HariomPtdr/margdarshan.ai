import { Building2, MapPin, Tag, Ticket } from "lucide-react";
import { useTranslation } from "react-i18next";

import type { PipelineState } from "../hooks/usePipeline";
import { PipelineSteps } from "./PipelineSteps";

interface Props {
  state: PipelineState;
  hasActiveComplaint: boolean;
}

const PRIORITY_COLOR: Record<string, string> = {
  Critical: "text-red-600 bg-red-50 border-red-200",
  High: "text-orange-600 bg-orange-50 border-orange-200",
  Med: "text-yellow-700 bg-yellow-50 border-yellow-200",
  Low: "text-gray-600 bg-gray-50 border-gray-200",
};

export function RightPanel({ state, hasActiveComplaint }: Props) {
  const { t } = useTranslation();

  if (!hasActiveComplaint) {
    return (
      <aside className="h-full bg-white border-l border-gray-200 p-6 flex items-center justify-center text-center">
        <div className="text-gray-400 text-sm">
          <div className="text-5xl mb-3">📋</div>
          {t("rightPanel.noActiveComplaint")}
        </div>
      </aside>
    );
  }

  const cls = state.classification;
  const route = state.routing;
  const sub = state.submission;
  const loc = state.location;
  const nlu = state.nluPayload;

  return (
    <aside className="h-full bg-white border-l border-gray-200 overflow-y-auto">
      <div className="px-4 py-3 border-b border-gray-200 sticky top-0 bg-white z-10">
        <h2 className="text-sm font-bold uppercase text-gray-600 tracking-wide">
          {t("rightPanel.title")}
        </h2>
      </div>

      <div className="p-4 space-y-5">
        <Section title={t("rightPanel.pipeline")}>
          <PipelineSteps state={state} />
        </Section>

        {loc && (
          <Section title={t("rightPanel.location")} icon={<MapPin size={14} />}>
            <p className="text-sm text-gray-800">{loc.address_text}</p>
            <p className="text-xs text-gray-500 mt-1">
              {loc.ward ? `${loc.ward} · ` : ""}
              {loc.pincode}
            </p>
          </Section>
        )}

        {nlu && (
          <Section title={t("rightPanel.extracted")} icon={<Tag size={14} />}>
            {nlu.keywords && nlu.keywords.length > 0 && (
              <div className="flex flex-wrap gap-1 mb-2">
                {nlu.keywords.slice(0, 8).map((k: string) => (
                  <span
                    key={k}
                    className="text-xs bg-saffron/10 text-saffron px-2 py-0.5 rounded-full"
                  >
                    {k}
                  </span>
                ))}
              </div>
            )}
            {nlu.entities?.phone?.length > 0 && (
              <Row label="Phone" value="•••• masked" />
            )}
          </Section>
        )}

        {cls && (
          <Section title={t("rightPanel.classified")}>
            <Row label={t("rightPanel.department")} value={cls.department} />
            <div className="flex items-center justify-between text-sm py-1">
              <span className="text-gray-500">{t("rightPanel.priority")}</span>
              <span
                className={`px-2 py-0.5 rounded-full text-xs font-semibold border ${
                  PRIORITY_COLOR[cls.priority] || PRIORITY_COLOR.Med
                }`}
              >
                {t(`priority.${cls.priority}`)}
              </span>
            </div>
            <Row label={t("rightPanel.sentiment")} value={t(`sentiment.${cls.sentiment}`)} />
            <Row
              label={t("rightPanel.confidence")}
              value={`${Math.round(cls.confidence * 100)}%`}
            />
          </Section>
        )}

        {route && (
          <Section title={t("rightPanel.portal")} icon={<Building2 size={14} />}>
            <p className="text-sm font-semibold text-gray-900">{route.portal_name}</p>
            <p className="text-xs text-gray-500 capitalize">{route.jurisdiction_level}</p>
          </Section>
        )}

        {sub && (
          <Section title={t("rightPanel.status")} icon={<Ticket size={14} />}>
            <Row label={t("rightPanel.ticket")} value={sub.portal_ticket_id} />
            <Row label="Status" value={sub.canonical_status} />
            <p className="text-xs text-govgreen mt-2 font-medium">
              {t("rightPanel.estimatedResponse")}
            </p>
          </Section>
        )}
      </div>
    </aside>
  );
}

function Section({
  title,
  icon,
  children,
}: {
  title: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="flex items-center gap-1.5 text-xs font-bold uppercase text-gray-500 tracking-wide mb-2">
        {icon}
        {title}
      </div>
      <div>{children}</div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between text-sm py-1">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium text-gray-900 truncate ml-3">{value}</span>
    </div>
  );
}
