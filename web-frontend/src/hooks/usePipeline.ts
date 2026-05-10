import { useEffect, useRef, useState } from "react";

import { pipelineWebSocket } from "../lib/api";
import type { PipelineEvent } from "../lib/types";

export interface PipelineState {
  stages: Record<string, "started" | "completed" | "failed" | "skipped" | "needs_clarification">;
  location?: any;
  nluPayload?: any;
  classification?: any;
  routing?: any;
  dedup?: any;
  submission?: any;
  trackerStatus?: any;
  // stage_6_filler: bot message pushed proactively by the pipeline (no user turn needed)
  fieldCollectionMessage?: string;
  fieldCollectionPortal?: string;
  fieldCollectionFields?: string[];
  clarifyingQuestion?: string;
}

const EMPTY: PipelineState = { stages: {} };

export function usePipeline(complaintId: string | undefined, seed?: PipelineState) {
  const [state, setState] = useState<PipelineState>(seed || EMPTY);
  const wsRef = useRef<WebSocket | null>(null);
  const seedRef = useRef(seed);
  seedRef.current = seed;

  useEffect(() => {
    if (!complaintId) {
      setState(EMPTY);
      return;
    }
    setState(seedRef.current || EMPTY);

    const ws = pipelineWebSocket(complaintId);
    wsRef.current = ws;

    ws.onmessage = (e) => {
      try {
        const evt: PipelineEvent = JSON.parse(e.data);
        setState((prev) => {
          const next: PipelineState = {
            ...prev,
            stages: { ...prev.stages, [evt.stage]: evt.status as any },
          };

          if (evt.stage === "stage_3_classify" && evt.status === "needs_clarification") {
            next.clarifyingQuestion = evt.payload?.clarifying_question;
            return next;
          }

          if (evt.status === "completed") {
            switch (evt.stage) {
              case "stage_1_intake":
                next.location = evt.payload.location;
                break;
              case "stage_2_nlu":
                next.nluPayload = evt.payload;
                break;
              case "stage_3_classify":
                next.classification = evt.payload;
                break;
              case "stage_5_route":
                next.routing = evt.payload;
                break;
              case "stage_7_dedup":
                next.dedup = evt.payload;
                break;
              case "stage_6_filler":
                // All fields collected — clear the pending field collection prompt.
                next.fieldCollectionMessage = undefined;
                break;
              case "stage_8_submit":
                next.submission = evt.payload;
                break;
              case "stage_10_status":
                next.trackerStatus = evt.payload;
                break;
            }
          }

          // stage_6_filler "started" carries a proactive bot message to show in chat.
          if (
            evt.stage === "stage_6_filler" &&
            evt.status === "started" &&
            evt.payload?.bot_message
          ) {
            next.fieldCollectionMessage = evt.payload.bot_message as string;
            next.fieldCollectionPortal  = evt.payload.portal_name as string | undefined;
            next.fieldCollectionFields  = evt.payload.required_fields as string[] | undefined;
          }

          return next;
        });
      } catch {}
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [complaintId]);

  return state;
}
