// ─── frontend/src/hooks/useAnalysis.ts ───────────────────────────────────────
// State machine for the full analysis lifecycle.
// Manages: idle → loading → success | error → idle (reset)

import { useCallback, useReducer } from "react";
import { analyzeRepo } from "../api/client";
import type { AnalysisState, AnalysisResult } from "../types";

// ─── Reducer ──────────────────────────────────────────────────────────────────

type Action =
  | { type: "START" }
  | { type: "SUCCESS"; payload: AnalysisResult }
  | { type: "ERROR";   payload: string }
  | { type: "RESET" };

const initialState: AnalysisState = {
  status: "idle",
  result: null,
  error:  null,
};

function reducer(state: AnalysisState, action: Action): AnalysisState {
  switch (action.type) {
    case "START":
      return { status: "loading", result: null,          error: null };
    case "SUCCESS":
      return { status: "success", result: action.payload, error: null };
    case "ERROR":
      return { status: "error",   result: null,          error: action.payload };
    case "RESET":
      return initialState;
    default:
      return state;
  }
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export interface UseAnalysisReturn {
  /** Current lifecycle status */
  status:   AnalysisState["status"];
  /** Full result when status === "success" */
  result:   AnalysisResult | null;
  /** Human-readable error when status === "error" */
  error:    string | null;
  /** Derived booleans for cleaner JSX */
  isLoading: boolean;
  isSuccess: boolean;
  isError:   boolean;
  /** Trigger an analysis. Safe to call multiple times. */
  analyze:  (url: string) => Promise<void>;
  /** Reset back to idle (e.g. when user clicks "Analyze another repo") */
  reset:    () => void;
}

export function useAnalysis(): UseAnalysisReturn {
  const [state, dispatch] = useReducer(reducer, initialState);

  const analyze = useCallback(async (url: string) => {
    // Guard: don't fire if already in-flight
    if (state.status === "loading") return;

    dispatch({ type: "START" });

    try {
      const result = await analyzeRepo(url);
      dispatch({ type: "SUCCESS", payload: result });
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : "An unexpected error occurred. Please try again.";
      dispatch({ type: "ERROR", payload: message });
    }
  }, [state.status]);

  const reset = useCallback(() => {
    dispatch({ type: "RESET" });
  }, []);

  return {
    status:    state.status,
    result:    state.result,
    error:     state.error,
    isLoading: state.status === "loading",
    isSuccess: state.status === "success",
    isError:   state.status === "error",
    analyze,
    reset,
  };
}