export interface Producto {
  id: number;
  nombre: string;
  marca: string;
  descripcion: string | null;
  stock: number;
  precio: number;
  imagen: string | null;
  categoria: CategoriaProducto;
}

export interface CategoriaProducto {
  id: number;
  nombre: string;
  slug: string;
}

export interface FiltrosCatalogo {
  categoria?: string;
  precio_min?: string;
  precio_max?: string;
  q?: string;
  orden?: "" | "precio_asc" | "precio_desc" | "nombre_asc";
}

export interface RespuestaCatalogo {
  productos: Producto[];
  categorias: CategoriaProducto[];
  total: number;
}

export * from "./auth";
export * from "./productos";
export * from "./carrito";
export * from "./api";
export * from "./pedidos";
export * from "./admin";
