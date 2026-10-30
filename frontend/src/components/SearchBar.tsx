import { useEffect, useId, useState } from "react";
import { FaSearch } from "react-icons/fa";
import { getProductos } from "../services/productos";
import type { Producto } from "../services";

const SearchBar: React.FC<{
  value: string;
  onChange: (v: string) => void;
  className?: string;
}> = ({ value, onChange, className = "w-80" }) => {
  const suggestionsId = useId();
  const [suggestions, setSuggestions] = useState<Producto[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  useEffect(() => {
    const query = value.trim();
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }

    let active = true;
    const timer = window.setTimeout(async () => {
      try {
        const result = await getProductos({ q: query });
        if (active) setSuggestions(result.productos.slice(0, 5));
      } catch {
        if (active) setSuggestions([]);
      }
    }, 180);

    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [value]);

  const selectSuggestion = (producto: Producto) => {
    onChange(producto.nombre);
    setIsOpen(false);
    setActiveIndex(-1);
  };

  return (
    <div className={`relative ${className}`}>
      <div className="flex items-center rounded-xl border border-white/10 bg-[#181a1b] px-3 py-2 transition focus-within:border-amber-500/70 focus-within:ring-2 focus-within:ring-amber-500/10">
        <FaSearch aria-hidden="true" className="mr-2 shrink-0 text-amber-500" />
        <input
          type="text"
          role="combobox"
          aria-label="Buscar productos"
          aria-autocomplete="list"
          aria-expanded={isOpen && suggestions.length > 0}
          aria-controls={suggestionsId}
          placeholder="Buscar productos o marcas..."
          value={value}
          onFocus={() => setIsOpen(true)}
          onChange={(event) => {
            onChange(event.target.value);
            setIsOpen(true);
            setActiveIndex(-1);
          }}
          onBlur={() => window.setTimeout(() => setIsOpen(false), 120)}
          onKeyDown={(event) => {
            if (!isOpen || suggestions.length === 0) return;
            if (event.key === "ArrowDown") {
              event.preventDefault();
              setActiveIndex((index) => (index + 1) % suggestions.length);
            } else if (event.key === "ArrowUp") {
              event.preventDefault();
              setActiveIndex((index) =>
                index <= 0 ? suggestions.length - 1 : index - 1
              );
            } else if (event.key === "Enter" && activeIndex >= 0) {
              event.preventDefault();
              selectSuggestion(suggestions[activeIndex]);
            } else if (event.key === "Escape") {
              setIsOpen(false);
            }
          }}
          className="w-full bg-transparent text-sm text-white outline-none placeholder:text-slate-500"
        />
      </div>
      {isOpen && suggestions.length > 0 && (
        <ul
          id={suggestionsId}
          role="listbox"
          className="absolute left-0 right-0 top-full z-50 mt-2 overflow-hidden rounded-xl border border-white/10 bg-[#17191b] p-1 shadow-2xl shadow-black/50"
        >
          {suggestions.map((producto, index) => (
            <li
              key={producto.id}
              role="option"
              aria-selected={index === activeIndex}
            >
              <button
                type="button"
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => selectSuggestion(producto)}
                className={`flex w-full items-center justify-between gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition ${
                  index === activeIndex
                    ? "bg-amber-500/15 text-amber-200"
                    : "text-slate-200 hover:bg-white/5"
                }`}
              >
                <span className="min-w-0">
                  <span className="block truncate font-medium">
                    {producto.nombre}
                  </span>
                  {producto.marca && (
                    <span className="mt-0.5 block truncate text-xs text-slate-500">
                      {producto.marca}
                    </span>
                  )}
                </span>
                <span className="shrink-0 text-xs text-slate-500">
                  {producto.categoria.nombre}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default SearchBar;
