import api from "./api";

export interface CarritoItem {
  id: number;
  nombre: string;
  precio: number;
  cantidad: number;
  imagen?: string;
}

export interface Carrito {
  [key: string]: CarritoItem;
}

export const getCarrito = async () => {
  try {
    const res = await api.get("/carrito/");
    return res.data;
  } catch (error) {
    console.error("Error al obtener el carrito:", error);
    throw error;
  }
};

export const agregarAlCarrito = async (
  productoId: number,
  cantidad: number = 1
) => {
  try {
    const res = await api.post(`/carrito/agregar/${productoId}/`, {
      cantidad,
    });
    return res.data;
  } catch (error) {
    console.error("Error al agregar al carrito:", error);
    throw error;
  }
};

export const eliminarDelCarrito = async (
  productoId: number,
  cantidad: number = 1
) => {
  try {
    const res = await api.post(`/carrito/eliminar/${productoId}/`, { cantidad });
    return res.data;
  } catch (error) {
    console.error("Error al eliminar del carrito:", error);
    throw error;
  }
};

export const vaciarCarrito = async () => {
  const res = await api.post("/carrito/vaciar/");
  return res.data;
};

export const confirmarCompra = async () => {
  try {
    const res = await api.post("/carrito/confirmar/");
    return res.data;
  } catch (error) {
    console.error("Error al confirmar compra:", error);
    throw error;
  }
};
