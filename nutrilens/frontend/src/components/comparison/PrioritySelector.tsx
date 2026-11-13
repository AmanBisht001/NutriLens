import React from "react";
import { Sparkles } from "lucide-react";
import type { ComparisonPriority } from "@/types";

interface PrioritySelectorProps {
  selectedPriorities: ComparisonPriority[];
  onChange: (priorities: ComparisonPriority[]) => void;
}

const AVAILABLE_PRIORITIES: { id: ComparisonPriority; label: string; icon: string }[] = [
  { id: "lower_sugar", label: "Lower Sugar", icon: "🍬" },
  { id: "lower_sodium", label: "Lower Sodium", icon: "🧂" },
  { id: "lower_saturated_fat", label: "Lower Saturated Fat", icon: "🥓" },
  { id: "higher_protein", label: "Higher Protein", icon: "💪" },
  { id: "higher_fibre", label: "Higher Fibre", icon: "🌾" },
  { id: "fewer_restriction_conflicts", label: "Fewer Restrictions Conflicts", icon: "🛡️" },
];

export const PrioritySelector: React.FC<PrioritySelectorProps> = ({
  selectedPriorities,
  onChange,
}) => {
  const togglePriority = (priority: ComparisonPriority) => {
    if (selectedPriorities.includes(priority)) {
      onChange(selectedPriorities.filter((p) => p !== priority));
    } else {
      onChange([...selectedPriorities, priority]);
    }
  };

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 space-y-3">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-emerald-600" />
          <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Comparison Priorities
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">
            {selectedPriorities.length === 0
              ? "Default criteria active"
              : `${selectedPriorities.length} active criteria`}
          </span>
          {selectedPriorities.length > 0 && (
            <button
              onClick={() => onChange([])}
              className="text-xs text-emerald-700 hover:text-emerald-800 font-medium underline"
            >
              Reset
            </button>
          )}
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {AVAILABLE_PRIORITIES.map((prio) => {
          const isSelected = selectedPriorities.includes(prio.id);
          return (
            <button
              key={prio.id}
              onClick={() => togglePriority(prio.id)}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all flex items-center gap-1.5 ${
                isSelected
                  ? "bg-emerald-600 text-white border-emerald-600 shadow-xs ring-2 ring-emerald-500/20"
                  : "bg-white text-slate-700 border-slate-200 hover:bg-slate-100/80"
              }`}
            >
              <span>{prio.icon}</span>
              <span>{prio.label}</span>
              {isSelected && (
                <span className="h-1.5 w-1.5 rounded-full bg-white ml-0.5 animate-pulse" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
};
