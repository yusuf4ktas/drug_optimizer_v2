import React, { useState } from 'react';
import {
  ChevronDown, ChevronUp, AlertTriangle,
  Activity, DollarSign, Clock, Shield
} from 'lucide-react';

export default function DrugCard({ drug, idx }) {
  const [expanded, setExpanded] = useState(false);

  // Parse Safety Color based on toxicity score
  const getSafetyColor = (score) => {
    if (score < 50) return 'text-emerald-600 bg-emerald-50 border-emerald-200';
    if (score < 150) return 'text-amber-600 bg-amber-50 border-amber-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  return (
    <div className="group transition-all duration-300 hover:bg-slate-50 border-l-4 border-transparent hover:border-emerald-500">
      <div
        onClick={() => setExpanded(!expanded)}
        className="p-5 cursor-pointer flex flex-col sm:flex-row gap-4 sm:items-center justify-between"
      >
        {/* Main Info */}
        <div className="flex-1 space-y-1">
          <div className="flex items-center gap-3">
            <span className="bg-slate-900 text-white text-xs font-bold px-2 py-1 rounded shadow-sm">
              #{idx + 1}
            </span>
            <h3 className="font-bold text-lg text-slate-800 group-hover:text-emerald-700 transition-colors">
              {drug.name}
            </h3>
            {/* Safety Badge */}
            <span className={`text-xs px-2 py-0.5 rounded-full border font-bold flex items-center gap-1 ${getSafetyColor(drug.toxicity_score)}`}>
              <Shield size={12} /> Safety Score: {drug.toxicity_score.toFixed(1)}
            </span>
          </div>

          <div className="flex flex-wrap gap-2 text-sm text-slate-500 items-center">
            {/* Conditions Covered */}
            {drug.covered_conditions && drug.covered_conditions.map((cond, i) => (
                <span key={i} className="text-emerald-700 bg-emerald-50/50 px-1.5 rounded text-xs font-semibold border border-emerald-100">
                    ✓ {cond}
                </span>
            ))}
          </div>
        </div>

        {/* Right: Metrics */}
        <div className="flex items-center gap-6 justify-between sm:justify-end min-w-[200px]">
           <div className="text-right">
              <div className="flex items-center justify-end gap-1 text-slate-400 text-xs font-bold uppercase tracking-wider">
                <Clock size={12} /> Half-Life
              </div>
              <div className="font-mono font-medium text-slate-700">
                {drug.half_life ? `${drug.half_life.toFixed(1)} hrs` : 'N/A'}
              </div>
           </div>

           <div className="text-right">
              <div className="flex items-center justify-end gap-1 text-slate-400 text-xs font-bold uppercase tracking-wider">
                <DollarSign size={12} /> Cost
              </div>
              <div className="font-mono font-bold text-emerald-600 text-lg">
                ${drug.price_val.toFixed(2)}
              </div>
           </div>

           <div className="text-slate-300">
             {expanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
           </div>
        </div>
      </div>

      {/* EXPANDED DETAILS */}
      {expanded && (
        <div className="px-5 pb-6 pt-0 animate-in slide-in-from-top-2 duration-200">
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 text-sm space-y-4">

                {/* Description */}
                <div>
                    <h4 className="font-bold text-slate-900 mb-1 flex items-center gap-2">
                        <Activity size={14} className="text-emerald-500"/> Mechanism of Action
                    </h4>
                    <p className="text-slate-600 leading-relaxed">
                        {drug.description || "No description available."}
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Enzymes (Metabolic Profile) */}
                    <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm">
                        <h4 className="font-bold text-slate-800 mb-2 text-xs uppercase tracking-wide">Metabolic Profile (Enzymes)</h4>
                        {drug.enzymes && drug.enzymes.length > 0 ? (
                            <ul className="space-y-1">
                                {drug.enzymes.map((e, i) => (
                                    <li key={i} className="flex justify-between items-center text-xs border-b border-slate-50 pb-1 last:border-0">
                                        <span className="font-mono text-slate-600 font-semibold">{e.enzyme_name}</span>
                                        <span className={`px-1.5 rounded ${e.inhibition_strength ? 'bg-red-50 text-red-600' : 'bg-slate-100 text-slate-500'}`}>
                                            {e.inhibition_strength || 'Substrate'}
                                        </span>
                                    </li>
                                ))}
                            </ul>
                        ) : <span className="text-slate-400 italic text-xs">No enzyme data found.</span>}
                    </div>

                    {/* Targets */}
                    <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm">
                        <h4 className="font-bold text-slate-800 mb-2 text-xs uppercase tracking-wide">Primary Targets</h4>
                         {drug.targets && drug.targets.length > 0 ? (
                            <div className="flex flex-wrap gap-1">
                                {drug.targets.map((t, i) => (
                                    <span key={i} className="bg-indigo-50 text-indigo-700 border border-indigo-100 px-2 py-0.5 rounded text-xs">
                                        {t.target_name}
                                    </span>
                                ))}
                            </div>
                        ) : <span className="text-slate-400 italic text-xs">No target data found.</span>}
                    </div>
                </div>

                {/* Warnings */}
                {drug.food_interactions && drug.food_interactions.length > 0 && (
                    <div className="flex gap-3 items-start p-3 bg-amber-50 border border-amber-100 rounded-lg text-amber-800">
                        <AlertTriangle size={16} className="mt-0.5 shrink-0" />
                        <div>
                            <span className="font-bold block text-xs uppercase mb-1">Interaction Warnings</span>
                            <ul className="list-disc list-inside space-y-0.5">
                                {drug.food_interactions.slice(0, 3).map((f, i) => (
                                    <li key={i}>{f}</li>
                                ))}
                            </ul>
                        </div>
                    </div>
                )}
            </div>
        </div>
      )}
    </div>
  );
}