import { CheckCircle2, Circle, Loader } from "lucide-react";
import { useTranslation } from "react-i18next";

import type { PipelineState } from "../hooks/usePipeline";

const ORDER = [
  "stage_0_chat",
  "stage_1_intake",
  "stage_2_nlu",
  "stage_3_classify",
  "stage_5_route",
  "stage_8_submit",
];

export function PipelineSteps({ state }: { state: PipelineState }) {
  const { t } = useTranslation();

  return (
    <div className="space-y-2">
      {ORDER.map((stage) => {
        const status = state.stages[stage];
        const label = t(`stages.${stage}`);
        return (
          <div key={stage} className="flex items-center gap-3 text-sm">
            {status === "completed" ? (
              <CheckCircle2 size={18} className="text-govgreen shrink-0" />
            ) : status === "started" ? (
              <Loader size={18} className="text-saffron shrink-0 animate-spin" />
            ) : (
              <Circle size={18} className="text-gray-300 shrink-0" />
            )}
            <span className={status ? "font-medium text-gray-900" : "text-gray-400"}>
              {label}
            </span>
          </div>
        );
      })}
    </div>
  );
}
