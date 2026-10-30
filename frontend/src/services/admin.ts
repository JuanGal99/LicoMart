import api from "./api";
import type { CategoriaProducto, Producto } from "./index";

export type EstadoPedido =
  | "Pendiente"
  | "En Proceso"
  | "Completado"
  | "Cancelado";

export interface AdminPedido {
  id: number;
  cliente: string;
  email: string;
  fecha: string;
  estado: EstadoPedido;
  pago_confirmado: boolean;
  fecha_pago: string | null;
  total: number;
  detalles: Array<{
    producto_id: number;
    producto: string;
    cantidad: number;
    precio_unitario: number;
    subtotal: number;
  }>;
}

export interface MovimientoInventario {
  id: number;
  producto_id: number;
  producto: string;
  tipo: "entrada" | "salida" | "ajuste";
  cantidad: number;
  stock_anterior: number;
  stock_nuevo: number;
  motivo: string;
  fecha: string;
  responsable: string;
}

export interface MovimientoFinanciero {
  id: number;
  tipo: "ingreso" | "egreso";
  concepto: string;
  importe: number;
  fecha: string;
  observaciones: string;
  pedido_id: number | null;
  responsable: string;
}

export interface DashboardData {
  kpis: {
    productos: number;
    unidades_inventario: number;
    ingresos: number;
    egresos: number;
    balance: number;
    pedidos_pendientes: number;
    pedidos_completados: number;
    pedidos_cancelados: number;
    ventas_pagadas: number;
    stock_bajo: number;
  };
  ventas_diarias: Array<{ fecha: string; ingresos: number; egresos: number }>;
  pedidos_recientes: AdminPedido[];
  movimientos_recientes: MovimientoInventario[];
  transacciones_recientes: MovimientoFinanciero[];
}

export interface ProductoPayload {
  nombre: string;
  marca: string;
  descripcion: string;
  categoria_id: number;
  precio: number;
  stock: number;
  imagen: string;
}

const requestKey = () => crypto.randomUUID();

export const prepareAdminSession = async () => {
  await api.get("/usuarios/csrf/");
};

export const getAdminDashboard = async () =>
  (await api.get<DashboardData>("/pedidos/admin/dashboard/")).data;

export const getAdminProductos = async (filters: {
  q?: string;
  categoria?: string;
  orden?: string;
} = {}) =>
  (await api.get<{ productos: Producto[]; categorias: CategoriaProducto[] }>(
    "/pedidos/admin/productos/",
    { params: filters }
  )).data;

export const createAdminProducto = async (payload: ProductoPayload) =>
  api.post("/pedidos/admin/productos/", payload);

export const updateAdminProducto = async (
  id: number,
  payload: ProductoPayload
) => api.patch(`/pedidos/admin/productos/${id}/`, payload);

export const deleteAdminProducto = async (id: number) =>
  api.delete(`/pedidos/admin/productos/${id}/`);

export const getAdminInventario = async () =>
  (await api.get<{
    productos: Array<{ id: number; nombre: string; stock: number }>;
    movimientos: MovimientoInventario[];
  }>("/pedidos/admin/inventario/")).data;

export const createAdminMovimientoInventario = async (payload: {
  producto_id: number;
  tipo: MovimientoInventario["tipo"];
  cantidad: number;
  motivo: string;
}) =>
  api.post("/pedidos/admin/inventario/", payload, {
    headers: { "Idempotency-Key": requestKey() },
  });

export const getAdminPedidos = async (filters: {
  estado?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
} = {}) =>
  (await api.get<{ pedidos: AdminPedido[] }>("/pedidos/admin/pedidos/", {
    params: filters,
  })).data.pedidos;

export const updateAdminPedido = async (id: number, estado: EstadoPedido) =>
  api.patch(`/pedidos/admin/pedidos/${id}/`, { estado });

export const confirmAdminPayment = async (id: number) =>
  api.post(`/pedidos/admin/pedidos/${id}/pago/`);

export const getAdminFinanzas = async (filters: {
  tipo?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
  q?: string;
} = {}) =>
  (await api.get<{ movimientos: MovimientoFinanciero[] }>(
    "/pedidos/admin/finanzas/",
    { params: filters }
  )).data.movimientos;

export const createAdminMovimientoFinanciero = async (payload: {
  tipo: "ingreso" | "egreso";
  concepto: string;
  importe: number;
  fecha: string;
  observaciones: string;
}) =>
  api.post("/pedidos/admin/finanzas/", payload, {
    headers: { "Idempotency-Key": requestKey() },
  });

export const getAdminMovimientos = async () =>
  (await api.get<{ movimientos: MovimientoInventario[] }>(
    "/pedidos/admin/movimientos/"
  )).data.movimientos;
