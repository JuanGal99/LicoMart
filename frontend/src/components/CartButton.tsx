import { useState, useEffect } from "react";
import { FiMinus, FiPlus, FiShoppingCart, FiTrash2 } from "react-icons/fi";
import {
  agregarAlCarrito,
  getCarrito,
  type Carrito,
  eliminarDelCarrito,
  confirmarCompra,
} from "../services/carrito";

const CartButton: React.FC = () => {
  const [carrito, setCarrito] = useState<Carrito>({});
  const [total, setTotal] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [updatingProduct, setUpdatingProduct] = useState<number | null>(null);
  const [clearing, setClearing] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    loadCarrito();

    const onUpdated = () => {
      loadCarrito();
    };
    window.addEventListener("carrito:updated", onUpdated);
    return () => {
      window.removeEventListener("carrito:updated", onUpdated);
    };
  }, []);

  const loadCarrito = async () => {
    try {
      const data = await getCarrito();
      setCarrito(data.carrito || {});
      setTotal(data.total || 0);
    } catch (error) {
      console.error("Error al cargar el carrito:", error);
    }
  };

  const toggleCarrito = () => setIsOpen((open) => !open);

  const handleCantidad = async (productoId: number, incremento: number) => {
    setUpdatingProduct(productoId);
    setError("");
    try {
      if (incremento > 0) {
        await agregarAlCarrito(productoId, 1);
      } else {
        await eliminarDelCarrito(productoId, 1);
      }
      await loadCarrito();
      window.dispatchEvent(new Event("carrito:updated"));
    } catch (error) {
      console.error("Error al actualizar la cantidad:", error);
      setError("No se pudo actualizar la cantidad. Inténtalo de nuevo.");
    } finally {
      setUpdatingProduct(null);
    }
  };

  const handleEliminar = async (productoId: number) => {
    const item = carrito[String(productoId)];
    if (!item) return;
    setUpdatingProduct(productoId);
    setError("");
    try {
      await eliminarDelCarrito(productoId, item.cantidad);
      await loadCarrito();
      window.dispatchEvent(new Event("carrito:updated"));
    } catch (error) {
      console.error("Error al eliminar del carrito:", error);
      setError("No se pudo eliminar el producto. Inténtalo de nuevo.");
    } finally {
      setUpdatingProduct(null);
    }
  };

  const handleVaciar = async () => {
    setClearing(true);
    setError("");
    try {
      for (const [productoId, item] of Object.entries(carrito)) {
        await eliminarDelCarrito(Number(productoId), item.cantidad);
      }
      await loadCarrito();
      window.dispatchEvent(new Event("carrito:updated"));
    } catch (error) {
      console.error("Error al vaciar el carrito:", error);
      setError("No se pudo vaciar todo el carrito. Inténtalo de nuevo.");
    } finally {
      setClearing(false);
    }
  };

  const handleConfirmar = async () => {
    if (Object.keys(carrito).length === 0) return;
    setSubmitting(true);
    try {
      await confirmarCompra();
      await loadCarrito();
      window.dispatchEvent(new Event("carrito:updated"));
    } catch (error) {
      console.error("Error al confirmar compra:", error);
      setError("No se pudo enviar el carrito. Inténtalo de nuevo.");
    } finally {
      setSubmitting(false);
    }
  };

  const cantidadTotal = Object.values(carrito).reduce(
    (cantidad, item) => cantidad + item.cantidad,
    0
  );

  return (
    <div className="relative">
      <button
        type="button"
        onClick={toggleCarrito}
        aria-label={`Carrito de compras, ${cantidadTotal} productos`}
        aria-expanded={isOpen}
        className="flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-white transition hover:border-amber-500/50 hover:bg-amber-500/10"
      >
        <FiShoppingCart className="text-lg text-amber-400" />
        {cantidadTotal > 0 && (
          <span className="rounded-full bg-amber-500 px-2 py-0.5 text-xs font-bold text-[#17130b]">
            {cantidadTotal}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full z-50 mt-3 w-80 max-w-[calc(100vw-2rem)] rounded-2xl border border-white/10 bg-[#17191b] shadow-2xl shadow-black/50 sm:w-96">
          <div className="p-4 sm:p-5">
            <h3 className="mb-4 font-semibold text-white">Tu carrito</h3>
            {Object.keys(carrito).length === 0 ? (
              <p className="rounded-xl bg-white/[0.03] px-4 py-6 text-center text-sm text-slate-400">
                El carrito está vacío
              </p>
            ) : (
              <div className="max-h-[55vh] space-y-3 overflow-y-auto">
                {Object.entries(carrito).map(([productoId, item]) => (
                  <div
                    key={productoId}
                    className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3 rounded-xl border border-white/5 bg-white/[0.03] p-3"
                  >
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        aria-label={`Disminuir cantidad de ${item.nombre}`}
                        disabled={updatingProduct !== null || clearing}
                        onClick={() => void handleCantidad(Number(productoId), -1)}
                        className="rounded-lg border border-white/10 p-1.5 text-slate-300 transition hover:border-amber-500/50 hover:text-amber-300 disabled:opacity-40"
                      >
                        <FiMinus aria-hidden="true" size={14} />
                      </button>
                      <span className="min-w-7 text-center text-sm font-semibold text-white">
                        {item.cantidad}
                      </span>
                      <button
                        type="button"
                        aria-label={`Aumentar cantidad de ${item.nombre}`}
                        disabled={updatingProduct !== null || clearing}
                        onClick={() => void handleCantidad(Number(productoId), 1)}
                        className="rounded-lg border border-white/10 p-1.5 text-slate-300 transition hover:border-amber-500/50 hover:text-amber-300 disabled:opacity-40"
                      >
                        <FiPlus aria-hidden="true" size={14} />
                      </button>
                    </div>
                    <div className="min-w-0 text-sm">
                      <p className="truncate font-medium text-slate-100">{item.nombre}</p>
                      <p className="mt-1 text-xs text-slate-400">
                        ${(item.precio * item.cantidad).toLocaleString("es-CO")}
                      </p>
                    </div>
                    <button
                      type="button"
                      aria-label={`Eliminar ${item.nombre} del carrito`}
                      disabled={updatingProduct !== null || clearing}
                      onClick={() => void handleEliminar(Number(productoId))}
                      className="rounded-lg border border-red-500/20 p-2 text-red-400 transition hover:border-red-500/50 hover:bg-red-500/10 hover:text-red-300 disabled:opacity-40"
                    >
                      <FiTrash2 aria-hidden="true" size={15} />
                    </button>
                  </div>
                ))}
                <div className="border-t border-white/10 pt-4">
                  {error && (
                    <p role="alert" className="mb-3 text-xs text-red-300">
                      {error}
                    </p>
                  )}
                  <div className="flex justify-between text-sm font-semibold text-white">
                    <span>Total</span>
                    <span className="text-amber-300">${total.toLocaleString("es-CO")}</span>
                  </div>
                  <button
                    type="button"
                    onClick={handleConfirmar}
                    disabled={submitting || clearing || updatingProduct !== null}
                    className="mt-4 w-full rounded-xl bg-amber-500 px-3 py-2.5 text-sm font-semibold text-[#19140a] transition hover:bg-amber-400 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {submitting ? "Enviando…" : "Enviar carrito"}
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleVaciar()}
                    disabled={clearing || submitting || updatingProduct !== null}
                    className="mt-2 w-full rounded-xl border border-red-500/20 px-3 py-2 text-sm font-medium text-red-300 transition hover:border-red-500/50 hover:bg-red-500/10 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {clearing ? "Vaciando…" : "Vaciar carrito"}
                  </button>
                </div>
              </div>
            )}
            {error && Object.keys(carrito).length === 0 && (
              <p role="alert" className="mt-3 text-xs text-red-300">{error}</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default CartButton;
