import axios from "axios";
import { useEffect, useRef, useState } from "react";
import {
  agregarAlCarrito,
  getCarrito,
  type Carrito,
} from "../services/carrito";
import { getProductos } from "../services/productos";
import type {
  CategoriaProducto,
  Producto,
  RespuestaCatalogo,
} from "../services";
import type { User } from "../services/auth";
import SearchBar from "../components/SearchBar";

type Props = {
  isLoggedIn: boolean;
  user: User | null;
  search: string;
  setSearch: (value: string) => void;
};

const formatPrice = (price: number) =>
  `$${price.toLocaleString("es-CO")}`;

function Home({ isLoggedIn, user, search, setSearch }: Props) {
  const [productos, setProductos] = useState<Producto[]>([]);
  const [categorias, setCategorias] = useState<CategoriaProducto[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [categoria, setCategoria] = useState("");
  const [precioMin, setPrecioMin] = useState("");
  const [precioMax, setPrecioMax] = useState("");
  const [orden, setOrden] = useState<
    "" | "precio_asc" | "precio_desc" | "nombre_asc"
  >("");
  const [addingToCart, setAddingToCart] = useState<number | null>(null);
  const [carritoCant, setCarritoCant] = useState<Record<number, number>>({});
  const [imagenesFallidas, setImagenesFallidas] = useState<
    Record<number, boolean>
  >({});
  const [reloadCount, setReloadCount] = useState(0);
  const hasLoadedCatalog = useRef(false);

  useEffect(() => {
    let active = true;
    const timer = window.setTimeout(async () => {
      if (!hasLoadedCatalog.current) setLoading(true);
      setError("");
      try {
        const data: RespuestaCatalogo = await getProductos({
          categoria,
          precio_min: precioMin,
          precio_max: precioMax,
          q: search.trim(),
          orden,
        });
        if (active) {
          setProductos(data.productos);
          setCategorias(data.categorias);
          setTotal(data.total);
          hasLoadedCatalog.current = true;
        }
      } catch (requestError) {
        if (active) {
          setError(
            axios.isAxiosError<{ error?: string }>(requestError)
              ? requestError.response?.data?.error || requestError.message
              : requestError instanceof Error
                ? requestError.message
                : "No se pudieron consultar los productos."
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    }, 200);

    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [categoria, precioMin, precioMax, search, orden, reloadCount]);

  useEffect(() => {
    const cargarCarrito = async () => {
      try {
        const data = await getCarrito();
        const carrito: Carrito = data.carrito || {};
        const cantidades: Record<number, number> = {};
        for (const [key, item] of Object.entries(carrito)) {
          cantidades[Number(key)] = item.cantidad || 0;
        }
        setCarritoCant(cantidades);
      } catch {
        setCarritoCant({});
      }
    };

    const onUpdated = () => {
      void cargarCarrito();
    };

    void cargarCarrito();
    window.addEventListener("carrito:updated", onUpdated);
    return () => window.removeEventListener("carrito:updated", onUpdated);
  }, []);

  const limpiarFiltros = () => {
    setCategoria("");
    setPrecioMin("");
    setPrecioMax("");
    setOrden("");
    setSearch("");
  };

  const handleAgregarAlCarrito = async (productoId: number) => {
    if (!isLoggedIn) {
      alert("Debes iniciar sesión para agregar productos al carrito");
      return;
    }

    setAddingToCart(productoId);
    try {
      await agregarAlCarrito(productoId, 1);
      window.dispatchEvent(new Event("carrito:updated"));
    } catch (requestError) {
      console.error("Error al agregar al carrito:", requestError);
      alert("Error al agregar el producto al carrito");
    } finally {
      setAddingToCart(null);
    }
  };

  const hayFiltros =
    Boolean(search.trim()) ||
    Boolean(categoria) ||
    Boolean(precioMin) ||
    Boolean(precioMax) ||
    Boolean(orden);

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#17140e] via-[#101316] to-[#0b0d0f] px-4 py-8 text-white sm:px-6 lg:px-8">
      <main className="mx-auto max-w-7xl">
        <header className="mb-8 flex flex-wrap items-end justify-between gap-4">
          {isLoggedIn && user && (
            <p className="text-sm text-slate-300">
              Bienvenido, <span className="font-semibold">{user.nombre}</span>
            </p>
          )}
        </header>

        <div className="grid items-start gap-6 lg:grid-cols-[17rem_minmax(0,1fr)]">
          <aside className="self-start lg:sticky lg:top-24 lg:max-h-[calc(100vh-7rem)] lg:overflow-y-auto">
            <section
              aria-label="Filtros del catálogo"
              className="rounded-2xl border border-white/10 bg-[#15181d]/95 p-4 shadow-xl shadow-black/20 backdrop-blur sm:p-5"
            >
              <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
                <h2 className="font-semibold">Encuentra lo que buscas</h2>
                <p className="text-sm text-slate-400" aria-live="polite">
                  {loading && productos.length === 0
                    ? "Cargando…"
                    : `${total} productos`}
                </p>
              </div>

              <div className="mb-4 md:hidden">
                <SearchBar
                  value={search}
                  onChange={setSearch}
                  className="w-full"
                />
              </div>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-1">
            <label className="text-xs font-medium text-slate-400">
              Categoría
              <select
                value={categoria}
                onChange={(event) => setCategoria(event.target.value)}
                className="mt-1.5 w-full rounded-xl border border-white/10 bg-[#0b0d0f] px-3 py-2.5 text-sm text-white outline-none transition focus:border-amber-500 focus:ring-2 focus:ring-amber-500/10"
              >
                <option value="">Todas las categorías</option>
                {categorias.map((item) => (
                  <option key={item.id} value={item.slug}>
                    {item.nombre}
                  </option>
                ))}
              </select>
            </label>

            <label className="text-xs font-medium text-slate-400">
              Precio mínimo
              <input
                type="number"
                min="0"
                step="1000"
                inputMode="numeric"
                value={precioMin}
                onChange={(event) => setPrecioMin(event.target.value)}
                placeholder="$ 0"
                className="mt-1.5 w-full rounded-xl border border-white/10 bg-[#0b0d0f] px-3 py-2.5 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-amber-500 focus:ring-2 focus:ring-amber-500/10"
              />
            </label>

            <label className="text-xs font-medium text-slate-400">
              Precio máximo
              <input
                type="number"
                min="0"
                step="1000"
                inputMode="numeric"
                value={precioMax}
                onChange={(event) => setPrecioMax(event.target.value)}
                placeholder="Sin límite"
                className="mt-1.5 w-full rounded-xl border border-white/10 bg-[#0b0d0f] px-3 py-2.5 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-amber-500 focus:ring-2 focus:ring-amber-500/10"
              />
            </label>

            <label className="text-xs font-medium text-slate-400">
              Ordenar por
              <select
                value={orden}
                onChange={(event) =>
                  setOrden(
                    event.target.value as
                      | ""
                      | "precio_asc"
                      | "precio_desc"
                      | "nombre_asc"
                  )
                }
                className="mt-1.5 w-full rounded-xl border border-white/10 bg-[#0b0d0f] px-3 py-2.5 text-sm text-white outline-none transition focus:border-amber-500 focus:ring-2 focus:ring-amber-500/10"
              >
                <option value="">Recomendados</option>
                <option value="precio_asc">Precio: menor a mayor</option>
                <option value="precio_desc">Precio: mayor a menor</option>
                <option value="nombre_asc">Nombre: A a Z</option>
              </select>
            </label>

            <button
              type="button"
              onClick={limpiarFiltros}
              disabled={!hayFiltros}
              className="self-end rounded-xl border border-white/10 px-4 py-2.5 text-sm font-medium text-slate-300 transition hover:border-amber-500/60 hover:bg-amber-500/5 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
            >
              Limpiar
            </button>
              </div>
            </section>
          </aside>

          <div className="min-w-0">
            {error ? (
          <section
            role="alert"
            className="rounded-2xl border border-red-500/30 bg-red-950/20 px-6 py-10 text-center"
          >
            <h2 className="text-lg font-semibold">No pudimos cargar el catálogo</h2>
            <p className="mt-2 text-sm text-red-200">{error}</p>
            <button
              type="button"
              onClick={() => setReloadCount((count) => count + 1)}
              className="mt-5 rounded-lg bg-amber-600 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-500"
            >
              Intentar de nuevo
            </button>
          </section>
            ) : loading && productos.length === 0 ? (
          <p className="py-16 text-center text-sm text-slate-400" role="status">
            Cargando productos…
          </p>
            ) : productos.length === 0 ? (
          <section className="rounded-2xl border border-white/10 bg-[#15181d] px-6 py-14 text-center">
            <h2 className="text-lg font-semibold">No hay productos con esos filtros</h2>
            <p className="mt-2 text-sm text-slate-400">
              Prueba con otra búsqueda o restablece los filtros del catálogo.
            </p>
            <button
              type="button"
              onClick={limpiarFiltros}
              className="mt-5 rounded-lg bg-amber-600 px-4 py-2 text-sm font-semibold text-white hover:bg-amber-500"
            >
              Limpiar filtros
            </button>
          </section>
            ) : (
              <section
                aria-label="Productos"
                className={`grid grid-cols-1 gap-5 transition-opacity sm:grid-cols-2 xl:grid-cols-3 ${
                  loading ? "opacity-70" : "opacity-100"
                }`}
              >
            {productos.map((producto) => {
              const stockDisponible = Math.max(
                0,
                producto.stock - (carritoCant[producto.id] || 0)
              );
              const imagenDisponible =
                producto.imagen && !imagenesFallidas[producto.id];

              return (
                <article
                  key={producto.id}
                  className="group flex flex-col overflow-hidden rounded-2xl border border-white/[0.08] bg-[#17191b] shadow-lg shadow-black/10 transition duration-200 hover:-translate-y-1 hover:border-amber-500/40 hover:shadow-xl hover:shadow-black/30"
                >
                  <div className="relative aspect-[4/3] overflow-hidden bg-slate-800">
                    {imagenDisponible ? (
                      <img
                        src={producto.imagen ?? undefined}
                        alt={`${producto.marca ? `${producto.marca} — ` : ""}${producto.nombre}`}
                        loading="lazy"
                        onError={() =>
                          setImagenesFallidas((fallidas) => ({
                            ...fallidas,
                            [producto.id]: true,
                          }))
                        }
                        className="h-full w-full object-cover transition duration-500 group-hover:scale-105"
                      />
                    ) : (
                      <div
                        role="img"
                        aria-label={`Imagen no disponible para ${producto.nombre}`}
                        className="flex h-full w-full flex-col items-center justify-center bg-gradient-to-br from-slate-800 to-[#15181d] text-slate-400"
                      >
                        <span className="text-3xl" aria-hidden="true">
                          ◇
                        </span>
                        <span className="mt-2 text-xs">Imagen no disponible</span>
                      </div>
                    )}
                    <span className="absolute left-3 top-3 rounded-full border border-white/10 bg-black/70 px-3 py-1 text-xs font-medium text-white backdrop-blur">
                      {producto.categoria.nombre}
                    </span>
                  </div>

                  <div className="flex flex-1 flex-col p-4">
                    {producto.marca && (
                      <p className="text-xs font-semibold uppercase tracking-[0.12em] text-amber-500">
                        {producto.marca}
                      </p>
                    )}
                    <h2 className="mt-1 text-base font-semibold leading-snug text-white">
                      {producto.nombre}
                    </h2>
                    <p className="mt-2 line-clamp-2 min-h-10 text-sm text-slate-400">
                      {producto.descripcion || "Descubre este producto en LicoMart."}
                    </p>

                    <div className="mt-auto flex items-end justify-between gap-3 pt-5">
                      <div>
                        <p className="text-xl font-bold text-white">
                          {formatPrice(producto.precio)}
                        </p>
                        <p className="mt-1 text-xs text-slate-500">
                          {stockDisponible > 0
                            ? `${stockDisponible} disponibles`
                            : "Agotado"}
                        </p>
                      </div>
                      {user?.rol !== "admin" && (
                        <button
                          type="button"
                          onClick={() => void handleAgregarAlCarrito(producto.id)}
                          disabled={
                            addingToCart === producto.id || stockDisponible <= 0
                          }
                          className="rounded-lg bg-amber-600 px-3 py-2.5 text-sm font-semibold text-white transition hover:bg-amber-500 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          {addingToCart === producto.id
                            ? "Agregando…"
                            : stockDisponible <= 0
                              ? "Sin stock"
                              : "Agregar"}
                        </button>
                      )}
                    </div>
                  </div>
                </article>
              );
            })}
              </section>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default Home;
