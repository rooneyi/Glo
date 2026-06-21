import { motion, AnimatePresence } from 'framer-motion';
import { useMemo, useState } from 'react';
import {
  Area,
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.06, delayChildren: 0.05 },
  },
};

const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 260, damping: 22 } },
};

const ACCENT = {
  green: 'border-l-green-500 bg-green-50/50',
  blue: 'border-l-blue-500 bg-blue-50/50',
  orange: 'border-l-orange-500 bg-orange-50/50',
  red: 'border-l-red-500 bg-red-50/50',
  purple: 'border-l-purple-500 bg-purple-50/50',
  teal: 'border-l-teal-500 bg-teal-50/50',
  indigo: 'border-l-indigo-500 bg-indigo-50/50',
  violet: 'border-l-violet-500 bg-violet-50/50',
  emerald: 'border-l-emerald-500 bg-emerald-50/50',
  sky: 'border-l-sky-500 bg-sky-50/50',
  amber: 'border-l-amber-500 bg-amber-50/50',
};

function KpiCard({ card }) {
  const accent = ACCENT[card.accent] || ACCENT.blue;
  return (
    <motion.div
      variants={item}
      whileHover={{ y: -3, boxShadow: '0 12px 24px -8px rgba(0,0,0,0.12)' }}
      className={`rounded-xl border border-zinc-200/80 border-l-4 ${accent} p-5 shadow-sm backdrop-blur-sm`}
    >
      <p className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500">{card.label}</p>
      <motion.p
        className="mt-2 text-2xl font-bold text-zinc-900 tabular-nums"
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.15, type: 'spring' }}
      >
        {card.value}
        {card.unit && <span className="ml-1 text-sm font-normal text-zinc-400">{card.unit}</span>}
      </motion.p>
      {card.sub && <p className="mt-1 text-xs text-zinc-500 leading-relaxed">{card.sub}</p>}
      {card.link && (
        <a href={card.link} className="mt-2 inline-block text-xs font-medium text-blue-600 hover:underline">
          Voir →
        </a>
      )}
    </motion.div>
  );
}

const CHART_TABS = [
  { id: 'production', label: 'Production', color: '#3b82f6' },
  { id: 'lots', label: 'Lots validés', color: '#10b981' },
  { id: 'livraisons', label: 'Livraisons', color: '#8b5cf6' },
  { id: 'labo', label: 'Laboratoire', color: '#6366f1' },
];

function ChartPanel({ stats, months }) {
  const [tab, setTab] = useState('production');

  const chartData = useMemo(() => {
    if (!stats?.rows) return [];
    const rows = stats.rows.slice(-months);
    return rows.map((r) => ({
      name: r.mois,
      productionKg: r.production_kg,
      productionNb: r.production_nb,
      lots: r.lots_valides,
      livraisonsSacs: r.livraisons_sacs,
      livraisonsNb: r.livraisons_nb,
      analyses: r.analyses_nb,
      conformes: r.analyses_conformes,
      echantillons: r.echantillons_nb,
    }));
  }, [stats, months]);

  const active = CHART_TABS.find((t) => t.id === tab);

  return (
    <motion.div variants={item} className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-zinc-900">Statistiques dynamiques</h3>
          <p className="text-xs text-zinc-400">Production par date de fin de mouture · {months} derniers mois</p>
        </div>
        <div className="flex flex-wrap gap-1 rounded-lg bg-zinc-100 p-1">
          {CHART_TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              className={`relative rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                tab === t.id ? 'text-zinc-900' : 'text-zinc-500 hover:text-zinc-700'
              }`}
            >
              {tab === t.id && (
                <motion.span
                  layoutId="chartTab"
                  className="absolute inset-0 rounded-md bg-white shadow-sm"
                  transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                />
              )}
              <span className="relative z-10">{t.label}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="h-[280px] w-full">
        <AnimatePresence mode="wait">
          <motion.div
            key={tab}
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -12 }}
            transition={{ duration: 0.25 }}
            className="h-full"
          >
            <ResponsiveContainer width="100%" height="100%">
              {tab === 'production' ? (
                <ComposedChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="gradProd" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} stroke="#a1a1aa" />
                  <YAxis yAxisId="kg" tick={{ fontSize: 10 }} stroke="#a1a1aa" />
                  <YAxis yAxisId="nb" orientation="right" tick={{ fontSize: 10 }} stroke="#a1a1aa" />
                  <Tooltip
                    contentStyle={{ borderRadius: 8, border: '1px solid #e4e4e7', fontSize: 12 }}
                  />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Area
                    yAxisId="kg"
                    type="monotone"
                    dataKey="productionKg"
                    name="Farine (kg)"
                    stroke="#3b82f6"
                    fill="url(#gradProd)"
                    animationDuration={800}
                  />
                  <Line
                    yAxisId="nb"
                    type="monotone"
                    dataKey="productionNb"
                    name="Moutures"
                    stroke="#f97316"
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    animationDuration={800}
                  />
                </ComposedChart>
              ) : tab === 'lots' ? (
                <ComposedChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12 }} />
                  <Bar dataKey="lots" name="Lots validés" fill="#10b981" radius={[4, 4, 0, 0]} animationDuration={700} />
                </ComposedChart>
              ) : tab === 'livraisons' ? (
                <ComposedChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12 }} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Bar dataKey="livraisonsSacs" name="Sacs livrés" fill="#8b5cf6" radius={[4, 4, 0, 0]} animationDuration={700} />
                  <Line type="monotone" dataKey="livraisonsNb" name="Bons retrait" stroke="#a78bfa" strokeWidth={2} dot={{ r: 3 }} />
                </ComposedChart>
              ) : (
                <ComposedChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f4f4f5" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip contentStyle={{ borderRadius: 8, fontSize: 12 }} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Bar dataKey="echantillons" name="Échantillons" fill="#c7d2fe" radius={[4, 4, 0, 0]} animationDuration={700} />
                  <Bar dataKey="analyses" name="Analyses" fill="#6366f1" radius={[4, 4, 0, 0]} animationDuration={700} />
                  <Line type="monotone" dataKey="conformes" name="Conformes" stroke="#10b981" strokeWidth={2} dot={{ r: 3 }} />
                </ComposedChart>
              )}
            </ResponsiveContainer>
          </motion.div>
        </AnimatePresence>
      </div>
      {active && (
        <p className="mt-2 text-center text-[10px] text-zinc-400">
          Graphique : {active.label} · survolez pour le détail
        </p>
      )}
    </motion.div>
  );
}

function SummaryStrip({ stats, months }) {
  if (!stats?.totaux) return null;
  const slice = stats.rows?.slice(-months) || [];
  const totals = slice.reduce(
    (acc, r) => ({
      production_kg: acc.production_kg + r.production_kg,
      production_nb: acc.production_nb + r.production_nb,
      lots_valides: acc.lots_valides + r.lots_valides,
      livraisons_sacs: acc.livraisons_sacs + r.livraisons_sacs,
      analyses_labo: acc.analyses_labo + r.analyses_nb,
    }),
    { production_kg: 0, production_nb: 0, lots_valides: 0, livraisons_sacs: 0, analyses_labo: 0 },
  );

  const chips = [
    { label: 'Production', value: `${Math.round(totals.production_kg)} kg`, sub: `${totals.production_nb} moutures`, color: 'text-blue-700 bg-blue-50' },
    { label: 'Lots validés', value: totals.lots_valides, color: 'text-emerald-700 bg-emerald-50' },
    { label: 'Livraisons', value: `${totals.livraisons_sacs} sacs`, color: 'text-violet-700 bg-violet-50' },
    { label: 'Analyses', value: totals.analyses_labo, color: 'text-indigo-700 bg-indigo-50' },
  ];

  return (
    <motion.div variants={item} className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {chips.map((c) => (
        <motion.div
          key={c.label}
          whileHover={{ scale: 1.02 }}
          className={`rounded-lg px-4 py-3 ${c.color}`}
        >
          <p className="text-[10px] font-semibold uppercase opacity-80">{c.label}</p>
          <p className="text-lg font-bold tabular-nums">{c.value}</p>
          {c.sub && <p className="text-[10px] opacity-70">{c.sub}</p>}
        </motion.div>
      ))}
    </motion.div>
  );
}

function MonthlyTable({ stats, months }) {
  const [open, setOpen] = useState(false);
  const rows = stats?.rows?.slice(-months) || [];

  return (
    <motion.div variants={item} className="overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-sm">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-5 py-4 text-left hover:bg-zinc-50"
      >
        <div>
          <h3 className="text-sm font-semibold text-zinc-900">Tableau mensuel</h3>
          <p className="text-xs text-zinc-400">Vue consolidée pour la prise de décision</p>
        </div>
        <motion.span animate={{ rotate: open ? 180 : 0 }} className="text-zinc-400">▼</motion.span>
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-x-auto border-t border-zinc-100"
          >
            <table className="w-full text-sm">
              <thead className="bg-zinc-50 text-xs uppercase text-zinc-500">
                <tr>
                  <th className="px-4 py-3 text-left">Mois</th>
                  <th className="px-4 py-3 text-right">Moutures</th>
                  <th className="px-4 py-3 text-right">Kg</th>
                  <th className="px-4 py-3 text-right">Lots</th>
                  <th className="px-4 py-3 text-right">Sacs</th>
                  <th className="px-4 py-3 text-right">Analyses</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {rows.map((r, i) => (
                  <motion.tr
                    key={r.mois_key}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.03 }}
                    className={i === rows.length - 1 ? 'bg-blue-50/40 font-medium' : 'hover:bg-zinc-50'}
                  >
                    <td className="px-4 py-2.5">{r.mois}</td>
                    <td className="px-4 py-2.5 text-right tabular-nums">{r.production_nb}</td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-blue-700">{Math.round(r.production_kg)}</td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-emerald-700">{r.lots_valides}</td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-violet-700">{r.livraisons_sacs}</td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-indigo-700">{r.analyses_nb}</td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function SidePanel({ alertes, activite, actions, urls }) {
  return (
    <div className="space-y-5">
      <motion.div variants={item} className="overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-zinc-100 px-5 py-4">
          <h3 className="text-sm font-semibold text-zinc-900">Alertes</h3>
          <a href={urls.alertes} className="text-xs text-blue-600 hover:underline">Tout voir</a>
        </div>
        <div className="max-h-64 divide-y divide-zinc-50 overflow-y-auto">
          {alertes.length === 0 && (
            <p className="px-5 py-8 text-center text-sm text-zinc-400">Aucune alerte</p>
          )}
          {alertes.map((a, i) => (
            <motion.div
              key={a.id}
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className={`px-5 py-3 ${!a.lu ? 'bg-blue-50/50' : ''}`}
            >
              <p className={`text-xs font-semibold ${a.typeClass}`}>{a.typeLabel}</p>
              <p className="mt-0.5 line-clamp-2 text-sm text-zinc-700">{a.message}</p>
              <p className="mt-1 text-[10px] text-zinc-400">{a.since}</p>
            </motion.div>
          ))}
        </div>
      </motion.div>

      <motion.div variants={item} className="overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-sm">
        <div className="border-b border-zinc-100 px-5 py-4">
          <h3 className="text-sm font-semibold text-zinc-900">Activité récente</h3>
        </div>
        <div className="divide-y divide-zinc-50">
          {activite.length === 0 && (
            <p className="px-5 py-8 text-center text-sm text-zinc-400">Aucune activité</p>
          )}
          {activite.map((e, i) => (
            <motion.div
              key={`${e.type}-${i}`}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: i * 0.06 }}
              className="px-5 py-3 hover:bg-zinc-50"
            >
              <p className="text-sm text-zinc-700">{e.description}</p>
              <p className="mt-0.5 text-[10px] text-zinc-400">{e.since} · {e.auteur}</p>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {actions.length > 0 && (
        <motion.div variants={item} className="overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-sm">
          <div className="border-b border-zinc-100 px-5 py-4">
            <h3 className="text-sm font-semibold text-zinc-900">Actions rapides</h3>
          </div>
          <div className="space-y-1 p-2">
            {actions.map((act) => (
              <motion.a
                key={act.href}
                href={act.href}
                whileHover={{ x: 4, backgroundColor: 'rgba(244,244,245,0.8)' }}
                className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-zinc-800"
              >
                <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-100 text-xs font-bold text-zinc-600">
                  {act.icon}
                </span>
                <span>
                  <span className="block font-medium">{act.label}</span>
                  {act.sub && <span className="block text-xs text-zinc-400">{act.sub}</span>}
                </span>
              </motion.a>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}

export default function Dashboard({ data }) {
  const [months, setMonths] = useState(12);
  const { kpiCards, stats, showStats, urls } = data;

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
      <motion.div variants={item} className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-zinc-900">Vue analytique</h2>
          <p className="text-sm text-zinc-500">{data.roleDisplay} · indicateurs en temps réel</p>
        </div>
        {showStats && (
          <div className="flex items-center gap-2 rounded-lg border border-zinc-200 bg-white p-1 shadow-sm">
            <span className="pl-2 text-xs text-zinc-500">Période</span>
            {[6, 12].map((m) => (
              <button
                key={m}
                type="button"
                onClick={() => setMonths(m)}
                className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                  months === m ? 'bg-blue-600 text-white shadow-sm' : 'text-zinc-600 hover:bg-zinc-100'
                }`}
              >
                {m} mois
              </button>
            ))}
            {urls.rapport && (
              <a href={urls.rapport} className="ml-1 pr-2 text-xs font-medium text-blue-600 hover:underline">
                Rapport →
              </a>
            )}
          </div>
        )}
      </motion.div>

      <motion.div variants={container} className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {kpiCards.map((card) => (
          <KpiCard key={card.id} card={card} />
        ))}
      </motion.div>

      {showStats && stats && (
        <div className="space-y-5">
          <SummaryStrip stats={stats} months={months} />
          <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
            <div className="xl:col-span-2">
              <ChartPanel stats={stats} months={months} />
            </div>
            <SidePanel
              alertes={data.alertes}
              activite={data.activite}
              actions={data.actions}
              urls={urls}
            />
          </div>
          <MonthlyTable stats={stats} months={months} />
        </div>
      )}

      {!showStats && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2" />
          <SidePanel
            alertes={data.alertes}
            activite={data.activite}
            actions={data.actions}
            urls={urls}
          />
        </div>
      )}
    </motion.div>
  );
}
