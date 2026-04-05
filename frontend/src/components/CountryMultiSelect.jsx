import { useEffect, useMemo, useRef, useState } from 'react'

const CONTINENT_ORDER = [
  'Africa',
  'America',
  'Asia',
  'Europe',
  'Oceania',
  'Antarctica',
]

/** country_converter uses "America" for the Americas */
const CONTINENT_LABEL = {
  Africa: 'Africa',
  America: 'Americas',
  Asia: 'Asia',
  Europe: 'Europe',
  Oceania: 'Oceania',
  Antarctica: 'Antarctica',
}

function groupCountriesForUi(items) {
  const byCont = {}
  for (const row of items) {
    const c = row.continent
    if (!byCont[c]) byCont[c] = []
    byCont[c].push(row.name)
  }
  for (const k of Object.keys(byCont)) {
    byCont[k].sort((a, b) => a.localeCompare(b))
  }
  return CONTINENT_ORDER.filter((c) => byCont[c]?.length).map((c) => ({
    continent: c,
    label: CONTINENT_LABEL[c] || c,
    names: byCont[c],
  }))
}

/**
 * Scrollable, continent-grouped multi-select (checkboxes).
 */
export default function CountryMultiSelect({
  label,
  hint,
  options,
  selected,
  onChange,
  placeholder = 'Select countries…',
}) {
  const [open, setOpen] = useState(false)
  const rootRef = useRef(null)

  const groups = useMemo(() => groupCountriesForUi(options || []), [options])

  useEffect(() => {
    if (!open) return
    const onDoc = (e) => {
      if (rootRef.current && !rootRef.current.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [open])

  const toggle = (name) => {
    const next = selected.includes(name)
      ? selected.filter((x) => x !== name)
      : [...selected, name]
    onChange(next)
  }

  const summary =
    selected.length === 0
      ? placeholder
      : `${selected.length} selected`

  return (
    <div ref={rootRef} className="relative">
      <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
      {hint ? <p className="text-xs text-gray-500 mb-1">{hint}</p> : null}
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between gap-2 px-3 py-2 text-left text-sm border border-gray-300 rounded-lg bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        aria-expanded={open}
        aria-haspopup="listbox"
      >
        <span className={selected.length === 0 ? 'text-gray-400' : 'text-gray-900'}>
          {summary}
        </span>
        <span className="text-gray-400 shrink-0" aria-hidden>
          ▾
        </span>
      </button>

      {selected.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {selected.map((name) => (
            <span
              key={name}
              className="inline-flex items-center gap-1 rounded-full bg-blue-50 text-blue-800 text-xs px-2 py-0.5 border border-blue-100"
            >
              {name}
              <button
                type="button"
                className="text-blue-600 hover:text-blue-900"
                onClick={() => toggle(name)}
                aria-label={`Remove ${name}`}
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      {open && (
        <div
          className="absolute z-30 mt-1 w-full rounded-lg border border-gray-200 bg-white shadow-lg max-h-72 overflow-y-auto overscroll-contain"
          role="listbox"
          aria-multiselectable="true"
        >
          {groups.length === 0 ? (
            <div className="px-3 py-4 text-sm text-gray-500 text-center">No countries available</div>
          ) : (
            groups.map((g) => (
              <div key={g.continent}>
                <div className="sticky top-0 z-10 bg-gray-100 px-3 py-2 text-xs font-semibold text-gray-700 border-b border-gray-200">
                  {g.label}
                </div>
                <ul className="py-1">
                  {g.names.map((name) => {
                    const checked = selected.includes(name)
                    return (
                      <li key={name}>
                        <label className="flex cursor-pointer items-center gap-2 px-3 py-1.5 text-sm hover:bg-gray-50">
                          <input
                            type="checkbox"
                            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            checked={checked}
                            onChange={() => toggle(name)}
                          />
                          <span className="text-gray-800">{name}</span>
                        </label>
                      </li>
                    )
                  })}
                </ul>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}
