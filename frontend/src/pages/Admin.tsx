import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line } from "react-chartjs-2";
import {
  FiActivity,
  FiAlertTriangle,
  FiBox,
  FiDollarSign,
  FiLogOut,
  FiPackage,
  FiShoppingBag,
  FiTrendingDown,
  FiTrendingUp,
} from "react-icons/fi";
import {
  clearUserFromStorage,
} from "../services/auth";
import {
  confirmAdminPayment,
  createAdminMovimientoFinanciero,
  createAdminMovimientoInventario,
  createAdminProducto,
  deleteAdminProducto,
  getAdminDashboard,
  getAdminFinanzas,
  getAdminInventario,
  getAdminMovimientos,
  getAdminPedidos,
  getAdminProductos,
  prepareAdminSession,
  updateAdminPedido,
  updateAdminProducto,
  type AdminPedido,
  type DashboardData,
  type EstadoPedido,
  type MovimientoFinanciero,
  type MovimientoInventario,
  type ProductoPayload,
} from "../services/admin";
import type { CategoriaProducto, Producto } from "../services";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Filler
);

type Section =
  | "dashboard"
  | "productos"
  | "inventario"
  | "pedidos"
  | "ingresos"
  | "egresos"
  | "movimientos";

const sections: Array<{ id: Section; label: string; icon: typeof FiActivity }> = [
  { id: "dashboard", label: "Dashboard", icon: FiActivity },
  { id: "productos", label: "Productos", icon: FiPackage },
  { id: "inventario", label: "Inventario", icon: FiBox },
  { id: "pedidos", label: "Ventas y pedidos", icon: FiShoppingBag },
  { id: "ingresos", label: "Ingresos", icon: FiTrendingUp },
  { id: "egresos", label: "Egresos", icon: FiTrendingDown },
  { id: "movimientos", label: "Movimientos", icon: FiActivity },
];

const emptyProduct = (): ProductoPayload => ({
  nombre: "",
  marca: "",
  descripcion: "",
  categoria_id: 0,
  precio: 0,
  stock: 0,
  imagen: "",
});

const money = (value: number) =>
  `$${value.toLocaleString("es-CO", { maximumFractionDigits: 0 })}`;

const errorMessage = (error: unknown) =>
  axios.isAxiosError<{ error?: string }>(error)
    ? error.response?.data?.error || error.message
    : error instanceof Error
      ? error.message
      : "Ocurrió un error inesperado.";

function groupChart(
  values: DashboardData["ventas_diarias"],
  period: "día" | "semana" | "mes"
) {
  const grouped = new Map<string, { income: number; expense: number }>();
  for (const row of values) {
    const date = new Date(`${row.fecha}T12:00:00`);
    let key = row.fecha;
    if (period === "semana") {
      date.setDate(date.getDate() - ((date.getDay() + 6) % 7));
      key = date.toISOString().slice(0, 10);
    } else if (period === "mes") {
      key = row.fecha.slice(0, 7);
    }
    const current = grouped.get(key) || { income: 0, expense: 0 };
    current.income += row.ingresos;
    current.expense += row.egresos;
    grouped.set(key, current);
  }
  return [...grouped.entries()].map(([fecha, values]) => ({
    fecha,
    ...values,
  }));
}

export default function Admin({ onLogout }: { onLogout: () => void }) {
  const navigate = useNavigate();
  const [section, setSection] = useState<Section>("dashboard");
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [products, setProducts] = useState<Producto[]>([]);
  const [categories, setCategories] = useState<CategoriaProducto[]>([]);
  const [orders, setOrders] = useState<AdminPedido[]>([]);
  const [inventory, setInventory] = useState<{
    productos: Array<{ id: number; nombre: string; stock: number }>;
    movimientos: MovimientoInventario[];
  }>({ productos: [], movimientos: [] });
  const [movements, setMovements] = useState<MovimientoInventario[]>([]);
  const [finance, setFinance] = useState<MovimientoFinanciero[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [chartPeriod, setChartPeriod] = useState<"día" | "semana" | "mes">("día");
  const [productQuery, setProductQuery] = useState("");
  const [productCategory, setProductCategory] = useState("");
  const [productOrder, setProductOrder] = useState("nombre_asc");
  const [editingProduct, setEditingProduct] = useState<number | null>(null);
  const [productForm, setProductForm] = useState<ProductoPayload>(emptyProduct);
  const [inventoryForm, setInventoryForm] = useState({
    producto_id: 0,
    tipo: "entrada" as MovimientoInventario["tipo"],
    cantidad: 1,
    motivo: "",
  });
  const [orderFilters, setOrderFilters] = useState({
    estado: "",
    fecha_desde: "",
    fecha_hasta: "",
  });
  const [financeFilters, setFinanceFilters] = useState({
    fecha_desde: "",
    fecha_hasta: "",
    q: "",
  });
  const [financeForm, setFinanceForm] = useState({
    concepto: "",
    importe: 0,
    fecha: new Date().toISOString().slice(0, 10),
    observaciones: "",
  });

  const handleUnauthorized = useCallback((requestError: unknown) => {
    if (axios.isAxiosError(requestError) && requestError.response?.status === 401) {
      clearUserFromStorage();
      navigate("/", { replace: true });
      return true;
    }
    return false;
  }, [navigate]);

  const loadDashboard = useCallback(async () => {
    const data = await getAdminDashboard();
    setDashboard(data);
  }, []);

  const loadProducts = useCallback(async () => {
    const result = await getAdminProductos({
      q: productQuery,
      categoria: productCategory,
      orden: productOrder,
    });
    setProducts(result.productos);
    setCategories(result.categorias);
  }, [productCategory, productOrder, productQuery]);

  const loadInventory = useCallback(async () => {
    const result = await getAdminInventario();
    setInventory(result);
    setMovements(result.movimientos);
  }, []);

  const loadOrders = useCallback(async () => {
    setOrders(await getAdminPedidos(orderFilters));
  }, [orderFilters]);

  const loadFinance = useCallback(async () => {
    const result = await getAdminFinanzas({
      ...financeFilters,
      tipo: section === "ingresos" ? "ingreso" : "egreso",
    });
    setFinance(result);
  }, [financeFilters, section]);

  useEffect(() => {
    let active = true;
    const initialize = async () => {
      setLoading(true);
      try {
        await prepareAdminSession();
        const [dashboardData, productData, inventoryData, orderData, financeData] =
          await Promise.all([
            getAdminDashboard(),
            getAdminProductos(),
            getAdminInventario(),
            getAdminPedidos(),
            getAdminFinanzas(),
          ]);
        if (!active) return;
        setDashboard(dashboardData);
        setProducts(productData.productos);
        setCategories(productData.categorias);
        setInventory(inventoryData);
        setMovements(inventoryData.movimientos);
        setOrders(orderData);
        setFinance(financeData);
      } catch (requestError) {
        if (!active) return;
        if (!handleUnauthorized(requestError)) setError(errorMessage(requestError));
      } finally {
        if (active) setLoading(false);
      }
    };
    void initialize();
    return () => {
      active = false;
    };
  }, [handleUnauthorized]);

  useEffect(() => {
    if (loading) return;
    if (section === "productos") void loadProducts().catch(setErrorFrom);
    if (section === "pedidos") void loadOrders().catch(setErrorFrom);
    if (section === "ingresos" || section === "egresos") {
      void loadFinance().catch(setErrorFrom);
    }
    if (section === "movimientos") {
      void getAdminMovimientos()
        .then(setMovements)
        .catch(setErrorFrom);
    }
    function setErrorFrom(requestError: unknown) {
      if (!handleUnauthorized(requestError)) setError(errorMessage(requestError));
    }
  }, [productCategory, productOrder, productQuery, orderFilters, financeFilters, section, loading, loadProducts, loadOrders, loadFinance, handleUnauthorized]);

  const chartRows = useMemo(
    () => groupChart(dashboard?.ventas_diarias || [], chartPeriod),
    [dashboard, chartPeriod]
  );
  const stockAlertProducts = inventory.productos.filter((item) => item.stock <= 5);

  const perform = async (action: () => Promise<unknown>, success: string) => {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await action();
      setNotice(success);
      await Promise.all([loadDashboard(), loadProducts(), loadInventory(), loadOrders(), loadFinance()]);
    } catch (requestError) {
      if (!handleUnauthorized(requestError)) setError(errorMessage(requestError));
    } finally {
      setBusy(false);
    }
  };

  const saveProduct = async (event: React.FormEvent) => {
    event.preventDefault();
    await perform(
      () => editingProduct
        ? updateAdminProducto(editingProduct, productForm)
        : createAdminProducto(productForm),
      editingProduct ? "Producto actualizado." : "Producto creado."
    );
    setEditingProduct(null);
    setProductForm(emptyProduct());
  };

  const editProduct = (product: Producto) => {
    setEditingProduct(product.id);
    setProductForm({
      nombre: product.nombre,
      marca: product.marca,
      descripcion: product.descripcion || "",
      categoria_id: product.categoria.id,
      precio: product.precio,
      stock: product.stock,
      imagen: product.imagen || "",
    });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const removeProduct = async (product: Producto) => {
    if (!window.confirm(`¿Eliminar "${product.nombre}"? Si tiene historial, el sistema lo impedirá.`)) return;
    await perform(() => deleteAdminProducto(product.id), "Producto eliminado.");
  };

  const submitInventory = async (event: React.FormEvent) => {
    event.preventDefault();
    await perform(
      () => createAdminMovimientoInventario(inventoryForm),
      "Movimiento de inventario registrado."
    );
    setInventoryForm({ ...inventoryForm, cantidad: 1, motivo: "" });
  };

  const submitFinance = async (event: React.FormEvent) => {
    event.preventDefault();
    const tipo = section === "ingresos" ? "ingreso" : "egreso";
    await perform(
      () => createAdminMovimientoFinanciero({ ...financeForm, tipo }),
      tipo === "ingreso" ? "Ingreso registrado." : "Egreso registrado."
    );
    setFinanceForm({ ...financeForm, concepto: "", importe: 0, observaciones: "" });
  };

  const changeOrderState = async (pedido: AdminPedido, estado: EstadoPedido) => {
    if (estado === "Cancelado" && !window.confirm(`¿Cancelar el pedido #${pedido.id}?`)) return;
    await perform(
      () => updateAdminPedido(pedido.id, estado),
      `Pedido #${pedido.id} actualizado.`
    );
  };

  const confirmPayment = async (pedido: AdminPedido) => {
    if (!window.confirm(`¿Confirmar que el pago de ${money(pedido.total)} del pedido #${pedido.id} fue recibido?`)) return;
    await perform(
      () => confirmAdminPayment(pedido.id),
      `Pago del pedido #${pedido.id} confirmado; ingreso registrado una sola vez.`
    );
  };

  const kpis = dashboard?.kpis;
  const cards = [
    { label: "Productos", value: kpis?.productos ?? 0, icon: FiPackage, tone: "text-amber-300" },
    { label: "Unidades disponibles", value: kpis?.unidades_inventario ?? 0, icon: FiBox, tone: "text-sky-300" },
    { label: "Ventas pagadas", value: kpis?.ventas_pagadas ?? 0, icon: FiShoppingBag, tone: "text-emerald-300" },
    { label: "Pedidos completados", value: kpis?.pedidos_completados ?? 0, icon: FiActivity, tone: "text-sky-300" },
    { label: "Pedidos cancelados", value: kpis?.pedidos_cancelados ?? 0, icon: FiActivity, tone: "text-slate-400" },
    { label: "Ingresos registrados", value: money(kpis?.ingresos ?? 0), icon: FiTrendingUp, tone: "text-emerald-300" },
    { label: "Egresos", value: money(kpis?.egresos ?? 0), icon: FiTrendingDown, tone: "text-rose-300" },
    { label: "Balance neto de caja", value: money(kpis?.balance ?? 0), icon: FiDollarSign, tone: (kpis?.balance ?? 0) >= 0 ? "text-amber-300" : "text-rose-300" },
    { label: "Pedidos pendientes", value: kpis?.pedidos_pendientes ?? 0, icon: FiActivity, tone: "text-orange-300" },
    { label: "Stock bajo (≤5)", value: kpis?.stock_bajo ?? 0, icon: FiAlertTriangle, tone: "text-rose-300" },
  ];

  return (
    <main className="min-h-screen bg-[#0b0d0f] px-4 py-6 text-white sm:px-6 lg:px-8">
      <div className="mx-auto max-w-[1500px]">
        <header className="mb-6 flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-white/10 bg-[#15181d] p-5">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-amber-400">LicoMart · Gestión</p>
            <h1 className="mt-1 text-2xl font-bold">Panel administrativo</h1>
            <p className="mt-1 text-sm text-slate-400">Ventas, inventario y finanzas en un solo lugar.</p>
          </div>
          <button
            type="button"
            onClick={() => {
              onLogout();
              navigate("/", { replace: true });
            }}
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-4 py-2 text-sm text-slate-200 transition hover:border-amber-500/40 hover:text-amber-200"
          >
            <FiLogOut aria-hidden="true" /> Cerrar sesión
          </button>
        </header>

        <nav aria-label="Secciones administrativas" className="mb-6 flex gap-2 overflow-x-auto rounded-2xl border border-white/10 bg-[#121416] p-2">
          {sections.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              onClick={() => {
                setSection(id);
                setError("");
                setNotice("");
              }}
              className={`inline-flex shrink-0 items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                section === id
                  ? "bg-amber-500 text-[#1b1608]"
                  : "text-slate-400 hover:bg-white/5 hover:text-white"
              }`}
            >
              <Icon aria-hidden="true" /> {label}
            </button>
          ))}
        </nav>

        {error && <div role="alert" className="mb-4 rounded-xl border border-red-500/30 bg-red-950/30 p-3 text-sm text-red-200">{error}</div>}
        {notice && <div role="status" className="mb-4 rounded-xl border border-emerald-500/30 bg-emerald-950/30 p-3 text-sm text-emerald-200">{notice}</div>}
        {loading ? (
          <p role="status" className="py-20 text-center text-slate-400">Cargando datos protegidos del panel…</p>
        ) : (
          <>
            {section === "dashboard" && (
              <section className="space-y-6">
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                  {cards.map(({ label, value, icon: Icon, tone }) => (
                    <article key={label} className="rounded-2xl border border-white/10 bg-[#15181d] p-4">
                      <div className="flex items-center justify-between">
                        <p className="text-sm text-slate-400">{label}</p>
                        <Icon aria-hidden="true" className={tone} size={19} />
                      </div>
                      <p className={`mt-3 text-2xl font-bold ${tone}`}>{value}</p>
                    </article>
                  ))}
                </div>

                <div className="grid gap-5 xl:grid-cols-[minmax(0,1.6fr)_minmax(18rem,1fr)]">
                  <section className="rounded-2xl border border-white/10 bg-[#15181d] p-5">
                    <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <h2 className="font-semibold">Ingresos y egresos</h2>
                        <p className="mt-1 text-xs text-slate-500">Movimientos reales registrados en los últimos 30 días.</p>
                      </div>
                      <select aria-label="Agrupar gráfico por" value={chartPeriod} onChange={(event) => setChartPeriod(event.target.value as typeof chartPeriod)} className="rounded-lg border border-white/10 bg-[#0b0d0f] px-3 py-2 text-sm">
                        <option value="día">Por día</option>
                        <option value="semana">Por semana</option>
                        <option value="mes">Por mes</option>
                      </select>
                    </div>
                    <Line
                      data={{
                        labels: chartRows.map((row) => row.fecha),
                        datasets: [
                          { label: "Ingresos", data: chartRows.map((row) => row.income), borderColor: "#34d399", backgroundColor: "rgba(52,211,153,.12)", fill: true, tension: 0.35 },
                          { label: "Egresos", data: chartRows.map((row) => row.expense), borderColor: "#fb7185", backgroundColor: "rgba(251,113,133,.08)", fill: true, tension: 0.35 },
                        ],
                      }}
                      options={{
                        responsive: true,
                        plugins: { legend: { labels: { color: "#cbd5e1" } } },
                        scales: {
                          x: { ticks: { color: "#94a3b8", maxTicksLimit: 10 }, grid: { color: "rgba(255,255,255,.04)" } },
                          y: { beginAtZero: true, ticks: { color: "#94a3b8", callback: (value) => `$${Number(value).toLocaleString("es-CO")}` }, grid: { color: "rgba(255,255,255,.06)" } },
                        },
                      }}
                    />
                    <p className="mt-2 text-xs text-slate-500">El balance mostrado es de caja; no representa utilidad neta.</p>
                  </section>
                  <section className="rounded-2xl border border-white/10 bg-[#15181d] p-5">
                    <h2 className="mb-4 font-semibold">Pedidos recientes</h2>
                    <div className="space-y-3">
                      {dashboard?.pedidos_recientes.map((pedido) => (
                        <div key={pedido.id} className="flex items-center justify-between gap-3 border-b border-white/5 pb-3 last:border-0">
                          <div className="min-w-0">
                            <p className="truncate text-sm font-medium">Pedido #{pedido.id} · {pedido.cliente}</p>
                            <p className="mt-1 text-xs text-slate-500">{pedido.fecha} · {pedido.pago_confirmado ? "Pago confirmado" : "Pago pendiente"}</p>
                          </div>
                          <span className="shrink-0 text-sm text-amber-200">{money(pedido.total)}</span>
                        </div>
                      ))}
                      {!dashboard?.pedidos_recientes.length && <p className="text-sm text-slate-500">Aún no hay pedidos.</p>}
                    </div>
                  </section>
                </div>

                <section className="grid gap-5 lg:grid-cols-2">
                  <div className="rounded-2xl border border-white/10 bg-[#15181d] p-5">
                    <h2 className="mb-4 font-semibold">Transacciones recientes</h2>
                    <div className="space-y-3">
                      {dashboard?.transacciones_recientes.map((item) => (
                        <div key={item.id} className="flex justify-between gap-3 text-sm">
                          <span className="min-w-0 truncate text-slate-300">{item.concepto}</span>
                          <span className={item.tipo === "ingreso" ? "shrink-0 text-emerald-300" : "shrink-0 text-rose-300"}>{item.tipo === "ingreso" ? "+" : "−"}{money(item.importe)}</span>
                        </div>
                      ))}
                      {!dashboard?.transacciones_recientes.length && <p className="text-sm text-slate-500">No hay movimientos financieros.</p>}
                    </div>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-[#15181d] p-5">
                    <h2 className="mb-4 font-semibold">Alertas de inventario</h2>
                    {stockAlertProducts.length ? (
                      <div className="space-y-2">
                        {stockAlertProducts.slice(0, 8).map((product) => (
                          <div key={product.id} className="flex justify-between text-sm">
                            <span className="text-slate-300">{product.nombre}</span>
                            <span className="font-semibold text-rose-300">{product.stock} unidades</span>
                          </div>
                        ))}
                      </div>
                    ) : <p className="text-sm text-emerald-300">No hay productos con stock bajo.</p>}
                  </div>
                </section>
                <MovementTable movements={dashboard?.movimientos_recientes || []} />
              </section>
            )}

            {section === "productos" && (
              <section className="space-y-5">
                <form onSubmit={saveProduct} className="grid gap-3 rounded-2xl border border-white/10 bg-[#15181d] p-5 sm:grid-cols-2 xl:grid-cols-4">
                  <h2 className="sm:col-span-2 xl:col-span-4 font-semibold">{editingProduct ? "Editar producto" : "Crear producto"}</h2>
                  <label className="text-xs text-slate-400">Nombre<input required maxLength={100} value={productForm.nombre} onChange={(e) => setProductForm({ ...productForm, nombre: e.target.value })} className="admin-input" /></label>
                  <label className="text-xs text-slate-400">Marca<input maxLength={100} value={productForm.marca} onChange={(e) => setProductForm({ ...productForm, marca: e.target.value })} className="admin-input" /></label>
                  <label className="text-xs text-slate-400">Categoría<select required value={productForm.categoria_id || ""} onChange={(e) => setProductForm({ ...productForm, categoria_id: Number(e.target.value) })} className="admin-input"><option value="">Selecciona</option>{categories.map((category) => <option key={category.id} value={category.id}>{category.nombre}</option>)}</select></label>
                  <label className="text-xs text-slate-400">Precio<input required type="number" min="1" step="0.01" value={productForm.precio || ""} onChange={(e) => setProductForm({ ...productForm, precio: Number(e.target.value) })} className="admin-input" /></label>
                  <label className="text-xs text-slate-400">Stock inicial{editingProduct && <span className="ml-1 text-slate-600">(usa Inventario para cambiar)</span>}<input required type="number" min="0" step="1" disabled={Boolean(editingProduct)} value={productForm.stock} onChange={(e) => setProductForm({ ...productForm, stock: Number(e.target.value) })} className="admin-input disabled:opacity-50" /></label>
                  <label className="text-xs text-slate-400">URL de imagen<input type="url" value={productForm.imagen} onChange={(e) => setProductForm({ ...productForm, imagen: e.target.value })} className="admin-input" /></label>
                  <label className="text-xs text-slate-400 sm:col-span-2">Descripción<textarea maxLength={200} value={productForm.descripcion} onChange={(e) => setProductForm({ ...productForm, descripcion: e.target.value })} className="admin-input min-h-20" /></label>
                  <div className="flex items-end gap-2">
                    <button disabled={busy} className="rounded-xl bg-amber-500 px-4 py-2.5 text-sm font-semibold text-[#19140a] disabled:opacity-50">{editingProduct ? "Guardar cambios" : "Crear producto"}</button>
                    {editingProduct && <button type="button" onClick={() => { setEditingProduct(null); setProductForm(emptyProduct()); }} className="rounded-xl border border-white/10 px-4 py-2.5 text-sm text-slate-300">Cancelar</button>}
                  </div>
                </form>

                <div className="rounded-2xl border border-white/10 bg-[#15181d] p-5">
                  <div className="mb-4 grid gap-3 sm:grid-cols-3">
                    <input aria-label="Buscar productos administrados" placeholder="Buscar nombre o marca" value={productQuery} onChange={(e) => setProductQuery(e.target.value)} className="admin-input" />
                    <select aria-label="Filtrar categoría" value={productCategory} onChange={(e) => setProductCategory(e.target.value)} className="admin-input"><option value="">Todas las categorías</option>{categories.map((category) => <option key={category.id} value={category.slug}>{category.nombre}</option>)}</select>
                    <select aria-label="Ordenar productos" value={productOrder} onChange={(e) => setProductOrder(e.target.value)} className="admin-input"><option value="nombre_asc">Nombre A-Z</option><option value="precio_asc">Precio menor a mayor</option><option value="precio_desc">Precio mayor a menor</option></select>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="admin-table"><thead><tr><th>Producto</th><th>Categoría</th><th>Precio</th><th>Stock</th><th>Acciones</th></tr></thead><tbody>
                      {products.map((product) => <tr key={product.id}><td><p className="font-medium text-white">{product.nombre}</p><p className="text-xs text-slate-500">{product.marca}</p></td><td>{product.categoria.nombre}</td><td>{money(product.precio)}</td><td>{product.stock}</td><td><div className="flex gap-2"><button type="button" onClick={() => editProduct(product)} className="text-amber-300 hover:text-amber-200">Editar</button><button type="button" onClick={() => void removeProduct(product)} className="text-rose-300 hover:text-rose-200">Eliminar</button></div></td></tr>)}
                      {!products.length && <tr><td colSpan={5}>No hay productos que coincidan.</td></tr>}
                    </tbody></table>
                  </div>
                </div>
              </section>
            )}

            {section === "inventario" && (
              <section className="space-y-5">
                {stockAlertProducts.length > 0 && <div className="flex items-center gap-2 rounded-xl border border-amber-500/20 bg-amber-500/5 p-3 text-sm text-amber-200"><FiAlertTriangle /> {stockAlertProducts.length} productos con cinco unidades o menos.</div>}
                <form onSubmit={submitInventory} className="grid gap-3 rounded-2xl border border-white/10 bg-[#15181d] p-5 sm:grid-cols-2 xl:grid-cols-4">
                  <h2 className="sm:col-span-2 xl:col-span-4 font-semibold">Registrar movimiento de stock</h2>
                  <label className="text-xs text-slate-400">Producto<select required value={inventoryForm.producto_id || ""} onChange={(e) => setInventoryForm({ ...inventoryForm, producto_id: Number(e.target.value) })} className="admin-input"><option value="">Selecciona producto</option>{inventory.productos.map((product) => <option key={product.id} value={product.id}>{product.nombre} · {product.stock} disponibles</option>)}</select></label>
                  <label className="text-xs text-slate-400">Tipo<select value={inventoryForm.tipo} onChange={(e) => setInventoryForm({ ...inventoryForm, tipo: e.target.value as typeof inventoryForm.tipo })} className="admin-input"><option value="entrada">Entrada</option><option value="salida">Salida</option><option value="ajuste">Ajuste a stock final</option></select></label>
                  <label className="text-xs text-slate-400">{inventoryForm.tipo === "ajuste" ? "Stock final" : "Cantidad"}<input required type="number" min="0" step="1" value={inventoryForm.cantidad} onChange={(e) => setInventoryForm({ ...inventoryForm, cantidad: Number(e.target.value) })} className="admin-input" /></label>
                  <label className="text-xs text-slate-400">Motivo obligatorio<input required maxLength={200} value={inventoryForm.motivo} onChange={(e) => setInventoryForm({ ...inventoryForm, motivo: e.target.value })} className="admin-input" /></label>
                  <button disabled={busy} className="self-end rounded-xl bg-amber-500 px-4 py-2.5 text-sm font-semibold text-[#19140a] disabled:opacity-50">Registrar movimiento</button>
                </form>
                <MovementTable movements={inventory.movimientos} />
              </section>
            )}

            {section === "pedidos" && (
              <section className="rounded-2xl border border-white/10 bg-[#15181d] p-5">
                <div className="mb-4 grid gap-3 sm:grid-cols-3">
                  <select aria-label="Filtrar estado" value={orderFilters.estado} onChange={(e) => setOrderFilters({ ...orderFilters, estado: e.target.value })} className="admin-input"><option value="">Todos los estados</option><option>Pendiente</option><option>En Proceso</option><option>Completado</option><option>Cancelado</option></select>
                  <label className="text-xs text-slate-400">Desde<input type="date" value={orderFilters.fecha_desde} onChange={(e) => setOrderFilters({ ...orderFilters, fecha_desde: e.target.value })} className="admin-input" /></label>
                  <label className="text-xs text-slate-400">Hasta<input type="date" value={orderFilters.fecha_hasta} onChange={(e) => setOrderFilters({ ...orderFilters, fecha_hasta: e.target.value })} className="admin-input" /></label>
                </div>
                <div className="overflow-x-auto"><table className="admin-table"><thead><tr><th>Pedido</th><th>Cliente</th><th>Fecha</th><th>Total</th><th>Pago</th><th>Estado / acciones</th></tr></thead><tbody>
                  {orders.map((order) => <tr key={order.id}><td>#{order.id}<details className="mt-1 text-xs"><summary className="cursor-pointer text-amber-300">Ver detalle ({order.detalles.length})</summary><ul className="mt-2 space-y-1">{order.detalles.map((item, index) => <li key={`${item.producto_id}-${index}`}>{item.cantidad} × {item.producto} · {money(item.precio_unitario)} c/u</li>)}</ul></details></td><td>{order.cliente}<span className="block text-xs text-slate-500">{order.email}</span></td><td>{order.fecha}</td><td>{money(order.total)}</td><td>{order.pago_confirmado ? <span className="text-emerald-300">Confirmado</span> : <button disabled={busy || order.estado === "Cancelado"} onClick={() => void confirmPayment(order)} className="text-amber-300 disabled:opacity-40">Confirmar pago</button>}</td><td><select aria-label={`Estado pedido ${order.id}`} disabled={busy || order.pago_confirmado} value={order.estado} onChange={(e) => void changeOrderState(order, e.target.value as EstadoPedido)} className="rounded-lg border border-white/10 bg-[#0b0d0f] px-2 py-1 text-xs">{["Pendiente", "En Proceso", "Completado", "Cancelado"].map((state) => <option key={state}>{state}</option>)}</select></td></tr>)}
                  {!orders.length && <tr><td colSpan={6}>No hay pedidos con esos filtros.</td></tr>}
                </tbody></table></div>
                <p className="mt-3 text-xs text-slate-500">El pago solo se confirma manualmente aquí. Al confirmarlo, Django registra el ingreso vinculado de forma idempotente.</p>
              </section>
            )}

            {(section === "ingresos" || section === "egresos") && (
              <section className="space-y-5">
                <form onSubmit={submitFinance} className="grid gap-3 rounded-2xl border border-white/10 bg-[#15181d] p-5 sm:grid-cols-2 xl:grid-cols-4">
                  <h2 className="sm:col-span-2 xl:col-span-4 font-semibold">Registrar {section === "ingresos" ? "otro ingreso" : "egreso"}</h2>
                  <label className="text-xs text-slate-400">Concepto<input required maxLength={160} value={financeForm.concepto} onChange={(e) => setFinanceForm({ ...financeForm, concepto: e.target.value })} className="admin-input" placeholder={section === "ingresos" ? "Otro ingreso (no registrar pagos de pedidos aquí)" : "Transporte, compra de mercancía…"} /></label>
                  <label className="text-xs text-slate-400">Importe<input required type="number" min="0.01" step="0.01" value={financeForm.importe || ""} onChange={(e) => setFinanceForm({ ...financeForm, importe: Number(e.target.value) })} className="admin-input" /></label>
                  <label className="text-xs text-slate-400">Fecha<input required type="date" value={financeForm.fecha} onChange={(e) => setFinanceForm({ ...financeForm, fecha: e.target.value })} className="admin-input" /></label>
                  <label className="text-xs text-slate-400">Observaciones<input maxLength={500} value={financeForm.observaciones} onChange={(e) => setFinanceForm({ ...financeForm, observaciones: e.target.value })} className="admin-input" /></label>
                  <button disabled={busy} className="self-end rounded-xl bg-amber-500 px-4 py-2.5 text-sm font-semibold text-[#19140a] disabled:opacity-50">Registrar {section === "ingresos" ? "ingreso" : "egreso"}</button>
                </form>
                {section === "ingresos" && <p className="text-xs text-slate-500">Los pagos de pedidos se registran desde Ventas y pedidos; evita duplicarlos como ingreso manual.</p>}
                <div className="grid gap-3 sm:grid-cols-3">
                  <label className="text-xs text-slate-400">Desde<input type="date" value={financeFilters.fecha_desde} onChange={(e) => setFinanceFilters({ ...financeFilters, fecha_desde: e.target.value })} className="admin-input" /></label>
                  <label className="text-xs text-slate-400">Hasta<input type="date" value={financeFilters.fecha_hasta} onChange={(e) => setFinanceFilters({ ...financeFilters, fecha_hasta: e.target.value })} className="admin-input" /></label>
                  <label className="text-xs text-slate-400">Concepto<input value={financeFilters.q} onChange={(e) => setFinanceFilters({ ...financeFilters, q: e.target.value })} className="admin-input" placeholder="Buscar concepto" /></label>
                </div>
                <FinanceTable movements={finance} />
              </section>
            )}

            {section === "movimientos" && <MovementTable movements={movements} />}
          </>
        )}
      </div>
      <style>{`
        .admin-input { display:block; width:100%; margin-top:.375rem; border:1px solid rgba(255,255,255,.1); border-radius:.75rem; background:#0b0d0f; padding:.65rem .75rem; color:#f8fafc; outline:none; }
        .admin-input:focus { border-color:rgba(245,158,11,.75); box-shadow:0 0 0 2px rgba(245,158,11,.1); }
        .admin-input option { background:#15181d; }
        .admin-table { width:100%; min-width:700px; border-collapse:collapse; text-align:left; font-size:.875rem; color:#cbd5e1; }
        .admin-table th { padding:.75rem; color:#94a3b8; font-weight:500; border-bottom:1px solid rgba(255,255,255,.1); }
        .admin-table td { padding:.75rem; border-bottom:1px solid rgba(255,255,255,.06); vertical-align:top; }
      `}</style>
    </main>
  );
}

function MovementTable({ movements }: { movements: MovimientoInventario[] }) {
  return (
    <section className="rounded-2xl border border-white/10 bg-[#15181d] p-5">
      <h2 className="mb-4 font-semibold">Historial de inventario</h2>
      <div className="overflow-x-auto"><table className="admin-table"><thead><tr><th>Fecha</th><th>Producto</th><th>Tipo</th><th>Cantidad</th><th>Stock antes → después</th><th>Motivo</th><th>Responsable</th></tr></thead><tbody>
        {movements.map((item) => <tr key={item.id}><td>{new Date(item.fecha).toLocaleString("es-CO")}</td><td>{item.producto}</td><td className="capitalize">{item.tipo}</td><td>{item.cantidad}</td><td>{item.stock_anterior} → {item.stock_nuevo}</td><td>{item.motivo}</td><td>{item.responsable}</td></tr>)}
        {!movements.length && <tr><td colSpan={7}>No hay movimientos registrados.</td></tr>}
      </tbody></table></div>
    </section>
  );
}

function FinanceTable({ movements }: { movements: MovimientoFinanciero[] }) {
  return (
    <section className="rounded-2xl border border-white/10 bg-[#15181d] p-5">
      <h2 className="mb-4 font-semibold">Historial financiero</h2>
      <div className="overflow-x-auto"><table className="admin-table"><thead><tr><th>Fecha</th><th>Tipo</th><th>Concepto</th><th>Importe</th><th>Pedido</th><th>Responsable</th></tr></thead><tbody>
        {movements.map((item) => <tr key={item.id}><td>{item.fecha}</td><td className="capitalize">{item.tipo}</td><td>{item.concepto}<span className="block text-xs text-slate-500">{item.observaciones}</span></td><td>{money(item.importe)}</td><td>{item.pedido_id ? `#${item.pedido_id}` : "—"}</td><td>{item.responsable}</td></tr>)}
        {!movements.length && <tr><td colSpan={6}>No hay movimientos financieros.</td></tr>}
      </tbody></table></div>
    </section>
  );
}
