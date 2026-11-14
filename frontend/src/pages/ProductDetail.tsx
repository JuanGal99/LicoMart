import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import axios from "axios";
import toast from "react-hot-toast";
import { getProducto } from "../services/productos";
import { agregarAlCarrito, getCarrito, type Carrito } from "../services/carrito";
import type { Producto } from "../services";
import type { User } from "../services/auth";

type Props = {
  isLoggedIn: boolean;
  user: User | null;
};

const formatPrice = (price: number) =>
  `$${price.toLocaleString("es-CO")}`;

function SkeletonDetail() {
  return (
    <div className="grid gap-8 lg:grid-cols-2">
      <div className="aspect-square animate-pulse rounded-2xl bg-slate-800" />
      <div className="flex flex-col gap-4">
        <div className="h-4 w-24 animate-pulse rounded bg-slate-700" />
        <div className="h-8 w-3/4 animate-pulse rounded bg-slate-700" />
        <div className="h-4 w-full animate-pulse rounded bg-slate-700/60" />
        <div className="h-4 w-2/3 animate-pulse rounded bg-slate-700/60" />
        <div className="mt-auto h-10 w-40 animate-pulse rounded-xl bg-slate-700" />
      </div>
    </div>
  );
}

export default function ProductDetail({ isLoggedIn, user }: Props) {
  const { id } = useParams<{ id: string }>();
  const [producto, setProducto] = useState<Producto | null>(null);
  const [relacionados, setRelacionados] = useState<Producto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [adding, setAdding] = useState(false);
  const [cartQty, setCartQty] = useState(0);
  const [imgError, setImgError] = useState(false);

  useEffect(() => {
    if (!id) return;
    let active = true;
    setLoading(true);
    setError("");
    setImgError(false);
    getProducto(Number(id))
      .then((data) => {
        if (!active) return;
        setProducto(data.producto);
        setRelacionados(data.relacionados);
      })
      .catch((err) => {
        if (!active) return;
        setError(
          axios.isAxiosError(err)
            ? err.response?.data?.error || err.message
            : "No se pudo cargar el producto."
        );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [id]);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await getCarrito();
        const carrito: Carrito = data.carrito || {};
        setCartQty(carrito[String(id)]?.cantidad || 0);
      } catch { /* ignore */ }
    };
    if (isLoggedIn) {
      void load();
    }
    const handler = () => void load();
    window.addEventListener("carrito:updated", handler);
    return () => window.removeEventListener("carrito:updated", handler);
  }, [id, isLoggedIn]);

  const handleAgregar = async () => {
    if (!isLoggedIn) {
      toast.error("Debes iniciar sesión para agregar productos al carrito");
      return;
    }
    if (!producto) return;
    setAdding(true);
    try {
      await agregarAlCarrito(producto.id, 1);
      window.dispatchEvent(new Event("carrito:updated"));
      toast.success("Producto agregado al carrito");
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.data?.error) {
        toast.error(err.response.data.error);
      } else {
        toast.error("Error al agregar al carrito");
      }
    } finally {
      setAdding(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-[#17140e] via-[#101316] to-[#0b0d0f] px-4 py-8 text-white sm:px-6 lg:px-8">
        <div className="mx-auto max-w-5xl">
          <SkeletonDetail />
        </div>
      </div>
    );
  }

  if (error || !producto) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-[#17140e] via-[#101316] to-[#0b0d0f] px-4 py-8 text-white sm:px-6 lg:px-8">
        <div className="mx-auto max-w-5xl text-center py-20">
          <h1 className="text-2xl font-bold">{error || "Producto no encontrado"}</h1>
          <Link to="/" className="mt-6 inline-block rounded-xl bg-amber-500 px-5 py-2.5 font-semibold text-[#19140a] transition hover:bg-amber-400">
            Volver al catálogo
          </Link>
        </div>
      </div>
    );
  }

  const stockDisponible = Math.max(0, producto.stock - cartQty);

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#17140e] via-[#101316] to-[#0b0d0f] px-4 py-8 text-white sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <nav className="mb-6 text-sm text-slate-400">
          <Link to="/" className="hover:text-amber-400 transition">Catálogo</Link>
          <span className="mx-2">/</span>
          <span className="text-slate-200">{producto.nombre}</span>
        </nav>

        <div className="grid gap-8 lg:grid-cols-2">
          <div className="aspect-square overflow-hidden rounded-2xl border border-white/10 bg-slate-800">
            {producto.imagen && !imgError ? (
              <img
                src={producto.imagen}
                alt={producto.nombre}
                onError={() => setImgError(true)}
                className="h-full w-full object-cover"
              />
            ) : (
              <div className="flex h-full w-full flex-col items-center justify-center bg-gradient-to-br from-slate-800 to-[#15181d] text-slate-400">
                <span className="text-5xl">◇</span>
                <span className="mt-3 text-sm">Imagen no disponible</span>
              </div>
            )}
          </div>

          <div className="flex flex-col">
            <span className="inline-block w-fit rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-slate-300">
              {producto.categoria.nombre}
            </span>
            {producto.marca && (
              <p className="mt-3 text-xs font-semibold uppercase tracking-[0.12em] text-amber-500">
                {producto.marca}
              </p>
            )}
            <h1 className="font-display mt-2 text-3xl font-bold">{producto.nombre}</h1>
            <p className="mt-4 leading-relaxed text-slate-400">
              {producto.descripcion || "Este producto aún no tiene una descripción detallada."}
            </p>

            <div className="mt-8">
              <p className="text-3xl font-bold text-amber-300">{formatPrice(producto.precio)}</p>
              <p className="mt-2 text-sm text-slate-500">
                {stockDisponible > 0 ? `${stockDisponible} disponibles` : "Agotado"}
              </p>
            </div>

            {user?.rol !== "admin" && (
              <button
                type="button"
                onClick={() => void handleAgregar()}
                disabled={adding || stockDisponible <= 0}
                className="mt-6 w-full rounded-xl bg-amber-500 px-6 py-3 text-base font-semibold text-[#19140a] transition hover:bg-amber-400 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
              >
                {adding ? "Agregando…" : stockDisponible <= 0 ? "Sin stock" : "Agregar al carrito"}
              </button>
            )}
          </div>
        </div>

        {relacionados.length > 0 && (
          <section className="mt-16">
            <h2 className="font-display mb-6 text-xl font-bold">Productos relacionados</h2>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              {relacionados.map((rel) => (
                <Link
                  key={rel.id}
                  to={`/producto/${rel.id}`}
                  className="group overflow-hidden rounded-2xl border border-white/[0.08] bg-[#17191b] transition hover:border-amber-500/40"
                >
                  <div className="aspect-[4/3] overflow-hidden bg-slate-800">
                    {rel.imagen ? (
                      <img src={rel.imagen} alt={rel.nombre} loading="lazy" className="h-full w-full object-cover transition duration-300 group-hover:scale-105" />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center text-2xl text-slate-600">◇</div>
                    )}
                  </div>
                  <div className="p-3">
                    <p className="truncate text-sm font-medium text-slate-200">{rel.nombre}</p>
                    <p className="mt-1 text-sm font-bold text-amber-300">{formatPrice(rel.precio)}</p>
                  </div>
                </Link>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
