import React, { useState } from 'react';
import {
  Plus, Trash2, ShieldCheck, Activity, Brain,
  FileText, List, Share2, LayoutGrid
} from 'lucide-react';

// Import Custom Components
import Alert from './components/Alert';
import SimpleGraph from './components/SimpleGraph';
import DrugCard from './components/DrugCard';

export default function App() {
  // --- State Management ---
  const [inputType, setInputType] = useState('list');
  const [input, setInput] = useState(''); // Current manual input field
  const [textInput, setTextInput] = useState(''); // NLP text area content
  const [conditions, setConditions] = useState([]);

  const [result, setResult] = useState(null);
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [mode, setMode] = useState('ilp'); // 'ilp' or 'greedy'
  const [view, setView] = useState('list'); // 'list' or 'graph' (results view)

  // --- Handlers ---

  const addCondition = (e) => {
    e.preventDefault();
    if (input.trim() && !conditions.includes(input.trim())) {
      setConditions([...conditions, input.trim()]);
      setInput('');
    }
  };

  const removeCondition = (cond) => {
    setConditions(conditions.filter(c => c !== cond));
  };

  const handleOptimize = async () => {
    // Basic Validation
    if (inputType === 'list' && conditions.length === 0) return;
    if (inputType === 'text' && textInput.trim().length === 0) return;

    setLoading(true);
    setError('');
    setResult(null);
    setGraphData(null);
    setView('list'); // Reset view to list on new search

    try {
      let data;
      let conditionsForGraph = conditions; // Default to manual list

      // Call the appropriate endpoint based on input type
      if (inputType === 'text') {
          // NLP Mode
          const response = await fetch('http://localhost:8000/optimize/text', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: textInput, mode }),
          });

          if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'NLP Analysis failed');
          }
          data = await response.json();

          // If NLP found entities, use them for the graph later
          if(data.nlp_source_entities && data.nlp_source_entities.length > 0) {
             conditionsForGraph = data.nlp_source_entities;
          }
      } else {
          // Manual List Mode
          const response = await fetch('http://localhost:8000/optimize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ conditions, mode }),
          });

          if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'Optimization failed');
          }
          data = await response.json();
      }

      setResult(data);

      // Fetch Graph Data (only if we have valid conditions found)
      if (data.status !== "No Entities Found" && conditionsForGraph.length > 0) {
        try {
            const graphRes = await fetch('http://localhost:8000/graph', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ conditions: conditionsForGraph, mode }),
            });
            if (graphRes.ok) {
                const gData = await graphRes.json();
                setGraphData(gData);
            }
        } catch (graphErr) {
            console.error("Graph fetch failed:", graphErr);
        }
      }

    } catch (err) {
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 p-6 font-sans">
      <div className="max-w-5xl mx-auto space-y-8">

        {/* HEADER */}
        <div className="text-center space-y-2 pt-8 animate-in fade-in slide-in-from-top-4 duration-700">
          <h1 className="text-4xl font-extrabold text-slate-900 flex justify-center items-center gap-3 tracking-tight">
            <ShieldCheck className="text-emerald-600" size={42} />
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-emerald-600 to-teal-700">
              PolyPharmacy
            </span>
            Optimizer
          </h1>
          <p className="text-slate-500 font-medium">Safe, Multi-Condition Drug Regimen Synthesis</p>
        </div>

        {/* MAIN INPUT CARD */}
        <div className="bg-white rounded-2xl shadow-lg shadow-slate-200/50 border border-slate-100 overflow-hidden transition-all duration-300">

          {/* Tab Switcher */}
          <div className="flex border-b border-slate-100">
             <button
                onClick={() => setInputType('list')}
                className={`flex-1 py-4 text-sm font-bold flex items-center justify-center gap-2 transition-all ${inputType === 'list' ? 'bg-emerald-50 text-emerald-700 border-b-2 border-emerald-500' : 'text-slate-400 hover:text-slate-600 hover:bg-slate-50'}`}
             >
                <List size={18} /> Manual List Entry
             </button>
             <button
                onClick={() => setInputType('text')}
                className={`flex-1 py-4 text-sm font-bold flex items-center justify-center gap-2 transition-all ${inputType === 'text' ? 'bg-indigo-50 text-indigo-700 border-b-2 border-indigo-500' : 'text-slate-400 hover:text-slate-600 hover:bg-slate-50'}`}
             >
                <Brain size={18} /> Clinical Note Analysis (NLP)
             </button>
          </div>

          <div className="p-8 space-y-6">

            {/* Manual Entry View */}
            {inputType === 'list' ? (
                <div className="space-y-4 animate-in fade-in duration-300">
                    <label className="block text-sm font-bold text-slate-700 uppercase tracking-wide">Patient Conditions List</label>
                    <form onSubmit={addCondition} className="flex gap-3">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="e.g. Ventricular arrhythmia"
                            className="flex-1 pl-4 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-none transition-all"
                        />
                        <button type="submit" className="bg-slate-900 text-white px-6 py-3 rounded-xl hover:bg-slate-800 transition-all font-semibold flex items-center gap-2 shadow-lg shadow-slate-900/20">
                            <Plus size={20} /> Add
                        </button>
                    </form>
                    <div className="flex flex-wrap gap-2 min-h-[40px]">
                        {conditions.length === 0 && <span className="text-slate-400 text-sm italic py-2">No conditions added yet...</span>}
                        {conditions.map((c, i) => (
                            <span key={i} className="bg-white text-emerald-700 pl-4 pr-2 py-1.5 rounded-full text-sm font-semibold flex items-center gap-2 border border-emerald-100 shadow-sm animate-in zoom-in-50 duration-200">
                                {c}
                                <button onClick={() => removeCondition(c)} className="w-6 h-6 rounded-full hover:bg-red-50 text-emerald-400 hover:text-red-500 flex items-center justify-center transition-colors">
                                    <Trash2 size={14} />
                                </button>
                            </span>
                        ))}
                    </div>
                </div>
            ) : (
                /* NLP View */
                <div className="space-y-4 animate-in fade-in duration-300">
                    <div className="flex justify-between items-center">
                        <label className="block text-sm font-bold text-indigo-900 uppercase tracking-wide">Clinical Notes / Patient Summary</label>
                        <span className="text-xs bg-indigo-100 text-indigo-700 px-2 py-1 rounded font-bold border border-indigo-200">BioBERT Model Active</span>
                    </div>
                    <textarea
                        value={textInput}
                        onChange={(e) => setTextInput(e.target.value)}
                        placeholder="Paste text here (e.g., 'The patient is a 45-year-old male presenting with severe migraines and symptoms of type 2 diabetes...')"
                        className="w-full h-32 pl-4 pr-4 py-3 bg-indigo-50/30 border border-indigo-100 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:outline-none transition-all resize-none text-slate-700 placeholder:text-slate-400"
                    />
                </div>
            )}

            {/* Controls & Submit */}
            <div className="flex flex-col sm:flex-row items-center justify-between pt-6 border-t border-slate-100 gap-4">
               {/* Algo Toggle */}
               <div className="flex items-center gap-6 bg-slate-50 px-4 py-2 rounded-lg border border-slate-200 w-full sm:w-auto justify-center sm:justify-start">
                 <label className="flex items-center gap-2 cursor-pointer hover:text-emerald-700 transition-colors">
                   <input type="radio" name="mode" value="ilp" checked={mode === 'ilp'} onChange={() => setMode('ilp')} className="w-4 h-4 accent-emerald-600" />
                   <span className="text-sm font-semibold text-slate-700">Safe Exact (ILP)</span>
                 </label>
                 <div className="w-px h-4 bg-slate-300"></div>
                 <label className="flex items-center gap-2 cursor-pointer hover:text-emerald-700 transition-colors">
                   <input type="radio" name="mode" value="greedy" checked={mode === 'greedy'} onChange={() => setMode('greedy')} className="w-4 h-4 accent-emerald-600" />
                   <span className="text-sm font-semibold text-slate-700">Fast Greedy</span>
                 </label>
              </div>

              {/* Action Button */}
              <button
                  onClick={handleOptimize}
                  disabled={loading || (inputType === 'list' && conditions.length === 0) || (inputType === 'text' && textInput.length === 0)}
                  className={`w-full sm:w-auto px-8 py-3 rounded-xl font-bold text-white shadow-lg transition-all flex items-center justify-center gap-2 
                    ${loading || (inputType === 'list' && conditions.length === 0) || (inputType === 'text' && textInput.length === 0)
                        ? 'bg-slate-300 cursor-not-allowed shadow-none' 
                        : 'bg-gradient-to-r from-emerald-500 to-teal-600 hover:shadow-emerald-500/30 hover:-translate-y-0.5 active:translate-y-0'}`}
              >
                  {loading && <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>}
                  {loading ? (inputType === 'text' ? 'Extracting & Optimizing...' : 'Processing...') : 'Generate Safe Regimen'}
              </button>
            </div>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
            <div className="animate-in slide-in-from-top-2 fade-in duration-300">
                <Alert variant="error">
                    <h3 className="font-bold">Optimization Failed</h3>
                    <p className="text-sm">{error}</p>
                </Alert>
            </div>
        )}

        {/* RESULTS SECTION */}
        {result && (
          <div className="space-y-6 animate-in slide-in-from-bottom-4 fade-in duration-500">

            {/* NLP Analysis Report */}
            {result.nlp_source_entities && result.nlp_source_entities.length > 0 && (
                <div className="bg-indigo-50 rounded-xl border border-indigo-100 p-5 flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="bg-indigo-100 p-2 rounded-lg text-indigo-600">
                            <FileText size={24} />
                        </div>
                        <div>
                            <h3 className="font-bold text-indigo-900">AI Analysis Report</h3>
                            <p className="text-xs text-indigo-700">BioBERT identified {result.nlp_source_entities.length} clinical conditions in your text.</p>
                        </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {result.nlp_source_entities.map((entity, i) => (
                            <span key={i} className="bg-white text-indigo-700 px-3 py-1 rounded-full text-sm font-bold shadow-sm border border-indigo-100 flex items-center gap-1">
                                <Activity size={12} /> {entity}
                            </span>
                        ))}
                    </div>
                </div>
            )}

            {/* Case: No Entities / Failure */}
            {result.status === "No Entities Found" ? (
               <Alert variant="info">
                  <h3 className="font-bold text-blue-800">No Medical Conditions Detected</h3>
                  <p className="text-sm text-blue-700 mt-1">
                    The AI model analyzed your text but could not confidently identify any specific medical conditions or diseases.
                    Please try rephrasing or adding specific condition names (e.g., "hypertension", "diabetes").
                  </p>
               </Alert>
            ) : (
               /* Case: Success */
               result.regimen ? (
                <>
                  {/* View Toggles */}
                  <div className="flex justify-center bg-white p-1.5 rounded-xl border border-slate-200 w-fit mx-auto shadow-sm">
                      <button
                        onClick={() => setView('list')}
                        className={`px-5 py-2 rounded-lg flex items-center gap-2 text-sm font-bold transition-all ${view === 'list' ? 'bg-slate-100 text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
                      >
                        <LayoutGrid size={18} /> Detailed List
                      </button>
                      <button
                        onClick={() => setView('graph')}
                        className={`px-5 py-2 rounded-lg flex items-center gap-2 text-sm font-bold transition-all ${view === 'graph' ? 'bg-slate-100 text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
                      >
                        <Share2 size={18} /> Network Graph
                      </button>
                  </div>

                  {/* List View Container */}
                  {view === 'list' && (
                      <div className="bg-white rounded-2xl shadow-xl shadow-slate-200/50 border border-slate-200 overflow-hidden animate-in fade-in duration-300">
                          {/* Summary Bar */}
                          <div className="bg-slate-50/50 px-8 py-5 border-b border-slate-200 flex flex-wrap gap-4 justify-between items-center">
                              <div>
                                  <h2 className="font-bold text-xl text-slate-800">Optimized Regimen</h2>
                                  <p className="text-xs text-slate-500 font-mono mt-1">Algorithm: {result.algorithm}</p>
                              </div>
                              <div className="flex gap-3">
                                  <div className="text-right">
                                      <span className="block text-xs text-slate-400 font-bold uppercase">Est. Cost</span>
                                      <span className="block font-mono font-bold text-emerald-600 text-lg">
                                        ${result.total_cost ? result.total_cost.toFixed(2) : '0.00'}
                                      </span>
                                  </div>
                                  <div className="text-right px-4 border-l border-slate-200">
                                      <span className="block text-xs text-slate-400 font-bold uppercase">Drugs</span>
                                      <span className="block font-mono font-bold text-slate-700 text-lg">{result.drug_count}</span>
                                  </div>
                              </div>
                          </div>

                          {/* Drug Cards List */}
                          <div className="divide-y divide-slate-100">
                              {result.regimen.length === 0 ? (
                                <div className="p-8 text-center text-slate-500 italic">No drugs found that match criteria.</div>
                              ) : (
                                result.regimen.map((drug, idx) => (
                                    <DrugCard key={idx} drug={drug} idx={idx} />
                                ))
                              )}
                          </div>
                      </div>
                  )}

                  {/* Graph View Container */}
                  {view === 'graph' && (
                      <div className="animate-in fade-in duration-300">
                          {graphData ? (
                            <SimpleGraph data={graphData} />
                          ) : (
                            <div className="h-[400px] flex items-center justify-center bg-white rounded-2xl border border-slate-200 text-slate-400">
                                <div className="text-center">
                                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-300 mx-auto mb-2"></div>
                                    <p>Building Network Graph...</p>
                                </div>
                            </div>
                          )}
                      </div>
                  )}
                </>
               ) : (
                <Alert variant="info">
                    No optimized regimen returned. Try adjusting your inputs.
                </Alert>
               )
            )}
          </div>
        )}
      </div>
    </div>
  );
}