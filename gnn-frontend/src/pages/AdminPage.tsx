import { useState } from 'react';
import { adminPatchPrices, type PriceEntry, type PatchResult } from '../services/api';
import { PlusCircle, Trash2, Send, TrendingUp, TrendingDown, Minus, Info, CheckCircle, AlertCircle, Loader } from 'lucide-react';

// ── helpers ────────────────────────────────────────────────────────────────────

function isWeekend(dateStr: string): boolean {
  const d = new Date(dateStr + 'T00:00:00');
  return d.getDay() === 0 || d.getDay() === 6;
}

function prevBusinessDay(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00');
  do { d.setDate(d.getDate() - 1); } while (d.getDay() === 0 || d.getDay() === 6);
  return d.toISOString().split('T')[0];
}

function todayStr(): string {
  return new Date().toISOString().split('T')[0];
}

function lastNBusinessDays(n: number): string[] {
  const days: string[] = [];
  let cur = todayStr();
  while (days.length < n) {
    if (!isWeekend(cur)) days.push(cur);
    cur = prevBusinessDay(cur);
  }
  return days.reverse();
}

// Pre-populate with the last 5 business days (today included)
function defaultRows(): PriceEntry[] {
  return lastNBusinessDays(5).map(date => ({ date, wti_price: 0, brent_price: 0 }));
}

// ── component ─────────────────────────────────────────────────────────────────

export default function AdminPage() {
  const [rows, setRows] = useState<PriceEntry[]>(defaultRows);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PatchResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // ── row management ──

  const updateRow = (idx: number, field: keyof PriceEntry, value: string) => {
    setRows(prev => {
      const next = [...prev];
      if (field === 'date') {
        next[idx] = { ...next[idx], date: value };
      } else {
        next[idx] = { ...next[idx], [field]: parseFloat(value) || 0 };
      }
      return next;
    });
  };

  const addRow = () => {
    const lastDate = rows.length > 0 ? rows[rows.length - 1].date : todayStr();
    const nextDate = prevBusinessDay(lastDate);
    setRows(prev => [{ date: nextDate, wti_price: 0, brent_price: 0 }, ...prev]);
  };

  const removeRow = (idx: number) => {
    setRows(prev => prev.filter((_, i) => i !== idx));
  };

  // ── submit ──

  const handleSubmit = async () => {
    const valid = rows.filter(r => r.date && r.wti_price > 0 && r.brent_price > 0);
    if (valid.length === 0) {
      setError('Enter at least one date with both WTI and Brent prices.');
      return;
    }
    // Warn on weekends
    const weekendDates = valid.filter(r => isWeekend(r.date)).map(r => r.date);
    if (weekendDates.length > 0) {
      setError(`Weekend dates detected: ${weekendDates.join(', ')}. Alpha Vantage is business-day only — remove these rows.`);
      return;
    }
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const res = await adminPatchPrices(valid);
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  // ── render ──

  const directionIcon = result?.predicted_direction === 'UP'
    ? <TrendingUp className="text-green-400" size={28} />
    : result?.predicted_direction === 'DOWN'
      ? <TrendingDown className="text-red-400" size={28} />
      : <Minus className="text-gray-400" size={28} />;

  const directionColor = result?.predicted_direction === 'UP'
    ? 'text-green-400'
    : result?.predicted_direction === 'DOWN'
      ? 'text-red-400'
      : 'text-gray-400';

  return (
    <div className="space-y-6 max-w-4xl mx-auto">

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Manual Price Override</h1>
        <p className="text-gray-400 mt-1 text-sm">
          Inject missing oil prices when Alpha Vantage data is lagged, then generate tomorrow's prediction.
        </p>
      </div>

      {/* Guide card */}
      <div className="glass rounded-xl p-5 border border-blue-500/20 bg-blue-500/5">
        <div className="flex items-start gap-3">
          <Info size={18} className="text-blue-400 mt-0.5 flex-shrink-0" />
          <div className="space-y-3 text-sm text-gray-300">
            <p className="font-semibold text-white">Which prices to use</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1">
                <p className="text-blue-300 font-medium">✓ Use (EIA Spot prices)</p>
                <ul className="space-y-1 text-gray-400 text-xs">
                  <li>• <span className="text-white">Twelve Data</span> — WTI/USD &amp; BRENT/USD, daily spot/continuous series</li>
                  <li>• <span className="text-white">EIA.gov</span> — official WTI &amp; Brent daily spot prices</li>
                  <li>• <span className="text-white">FRED / St. Louis Fed</span> — DCOILWTICO &amp; DCOILBRENTEU series</li>
                </ul>
              </div>
              <div className="space-y-1">
                <p className="text-red-300 font-medium">✗ Avoid (Futures prices)</p>
                <ul className="space-y-1 text-gray-400 text-xs">
                  <li>• Investing.com "Crude Oil WTI Futures" front-month</li>
                  <li>• CME/NYMEX CL futures settlements</li>
                  <li>• Bloomberg "CLc1" or "COc1" tickers</li>
                </ul>
              </div>
            </div>
            <div className="border-t border-white/10 pt-3 text-xs text-gray-400 space-y-1">
              <p>• <span className="text-white">Skip weekends</span> — Alpha Vantage only has business-day entries. Do not enter Sat/Sun rows.</p>
              <p>• Enter <span className="text-white">closing spot price</span> for each business day (USD per barrel).</p>
              <p>• Today's in-progress bar is fine to include — the model will use it as the latest reference close.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Price input table */}
      <div className="glass rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-white font-semibold">Price Entries</h2>
          <button
            onClick={addRow}
            className="flex items-center gap-1.5 text-sm text-blue-400 hover:text-blue-300 transition-colors"
          >
            <PlusCircle size={16} /> Add row
          </button>
        </div>

        {/* Column headers */}
        <div className="grid grid-cols-[1fr_140px_140px_36px] gap-3 text-xs text-gray-400 uppercase tracking-wider mb-2 px-1">
          <span>Date</span>
          <span>WTI ($/bbl)</span>
          <span>Brent ($/bbl)</span>
          <span />
        </div>

        <div className="space-y-2">
          {rows.map((row, idx) => {
            const weekend = row.date && isWeekend(row.date);
            return (
              <div
                key={idx}
                className={`grid grid-cols-[1fr_140px_140px_36px] gap-3 items-center ${weekend ? 'opacity-60' : ''}`}
              >
                <div className="relative">
                  <input
                    type="date"
                    value={row.date}
                    onChange={e => updateRow(idx, 'date', e.target.value)}
                    className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                  />
                  {weekend && (
                    <span className="absolute -top-1.5 right-2 text-[10px] bg-red-500/80 text-white px-1 rounded">weekend</span>
                  )}
                </div>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="e.g. 89.34"
                  value={row.wti_price || ''}
                  onChange={e => updateRow(idx, 'wti_price', e.target.value)}
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                />
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  placeholder="e.g. 100.45"
                  value={row.brent_price || ''}
                  onChange={e => updateRow(idx, 'brent_price', e.target.value)}
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                />
                <button
                  onClick={() => removeRow(idx)}
                  className="p-2 text-gray-500 hover:text-red-400 transition-colors rounded"
                >
                  <Trash2 size={15} />
                </button>
              </div>
            );
          })}
        </div>

        {rows.length === 0 && (
          <p className="text-center text-gray-500 text-sm py-6">No rows. Click "Add row" to start.</p>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-start gap-2 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-300 text-sm">
          <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Submit */}
      <button
        onClick={handleSubmit}
        disabled={loading}
        className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
      >
        {loading
          ? <><Loader size={16} className="animate-spin" /> Processing… (may take ~60s)</>
          : <><Send size={16} /> Inject Prices &amp; Run Prediction</>
        }
      </button>

      {/* Result */}
      {result && (
        <div className="glass rounded-xl p-6 border border-green-500/20 bg-green-500/5 space-y-5">
          <div className="flex items-center gap-2 text-green-400">
            <CheckCircle size={18} />
            <span className="font-semibold">Prediction Generated</span>
          </div>

          {/* Main result row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="glass p-4 rounded-lg text-center">
              <p className="text-xs text-gray-400 mb-1">Feature date</p>
              <p className="text-white font-semibold">{result.date}</p>
            </div>
            <div className="glass p-4 rounded-lg text-center">
              <p className="text-xs text-gray-400 mb-1">Today's WTI</p>
              <p className="text-white font-semibold">${result.reference_wti?.toFixed(2) ?? '—'}</p>
            </div>
            <div className="glass p-4 rounded-lg text-center">
              <p className="text-xs text-gray-400 mb-1">Predicted delta</p>
              <p className={`font-bold text-lg ${directionColor}`}>
                {result.predicted_delta > 0 ? '+' : ''}{result.predicted_delta.toFixed(4)}
              </p>
            </div>
            <div className="glass p-4 rounded-lg text-center">
              <p className="text-xs text-gray-400 mb-1">Tomorrow's est. WTI</p>
              <p className={`font-bold text-lg ${directionColor}`}>
                ${((result.reference_wti ?? 0) + result.predicted_delta).toFixed(2)}
              </p>
            </div>
          </div>

          {/* Direction banner */}
          <div className={`flex items-center justify-center gap-3 py-3 rounded-lg
            ${result.predicted_direction === 'UP' ? 'bg-green-500/10 border border-green-500/20'
              : result.predicted_direction === 'DOWN' ? 'bg-red-500/10 border border-red-500/20'
              : 'bg-gray-500/10 border border-gray-500/20'}`}>
            {directionIcon}
            <span className={`text-2xl font-bold ${directionColor}`}>
              {result.predicted_direction}
            </span>
          </div>

          {/* Top contributors */}
          {result.top_contributors && Object.keys(result.top_contributors).length > 0 && (
            <div>
              <p className="text-xs text-gray-400 uppercase tracking-wider mb-2">Top 5 Contributing Countries</p>
              <div className="space-y-1">
                {Object.entries(result.top_contributors).slice(0, 5).map(([country, info]) => (
                  <div key={country} className="flex items-center justify-between text-sm">
                    <span className="text-white font-medium w-12">{country}</span>
                    <div className="flex-1 mx-3 h-1.5 bg-white/10 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${info.contribution >= 0 ? 'bg-green-500' : 'bg-red-500'}`}
                        style={{ width: `${Math.min(info.percentage * 2, 100)}%` }}
                      />
                    </div>
                    <span className={`w-20 text-right ${info.contribution >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {info.contribution >= 0 ? '+' : ''}{info.contribution.toFixed(4)}
                    </span>
                    <span className="w-12 text-right text-gray-400">{info.percentage.toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Meta */}
          <div className="flex flex-wrap gap-3 text-xs text-gray-500">
            <span>Model: {result.model_version}</span>
            <span>Countries: {result.num_countries}</span>
            <span>Injected: {result.injected_dates.join(', ')}</span>
            <span>GCS: {result.gcs_file}</span>
          </div>
        </div>
      )}
    </div>
  );
}
