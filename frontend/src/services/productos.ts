import api from "./api";
import type { FiltrosCatalogo, Producto, RespuestaCatalogo } from "./index";

export const getProductos = async (
  filtros: FiltrosCatalogo = {}
): Promise<RespuestaCatalogo> => {
  try {
    const params = Object.fromEntries(
      Object.entries(filtros).filter(([, value]) => value !== undefined && value !== "")
    );
    const res = await api.get<RespuestaCatalogo>("/productos/", { params });
    return res.data;
  } catch (error) {
    console.error("Error al cargar productos:", error);
    throw error;
  }
};

export const getProducto = async (
  id: number
): Promise<{ producto: Producto; relacionados: Producto[] }> => {
  const res = await api.get<{ producto: Producto; relacionados: Producto[] }>(
    `/productos/${id}/`
  );
  return res.data;
};
