import { useState } from "react";
import {
  registerUser,
  loginUser,
  saveUserToStorage,
  type User,
} from "../services/auth";
import { FaEnvelope, FaLock, FaUser } from "react-icons/fa";

type Props = {
  visible: boolean;
  onClose: () => void;
  onLoginSuccess: () => void;
};

const AuthModal: React.FC<Props> = ({ visible, onClose, onLoginSuccess }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [form, setForm] = useState({
    identifier: "",
    password: "",
    username: "",
    email: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (!visible) return null;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const resetForm = () => setForm({ identifier: "", password: "", username: "", email: "" });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (isLogin) {
        const data = await loginUser(form.identifier, form.password);
        if (data.success) {
          const user: User = {
            id: data.usuario_id,
            nombre: data.nombre || form.identifier,
            email: data.email || (form.identifier.includes("@") ? form.identifier : ""),
            rol: data.rol || "usuario",
          };
          saveUserToStorage(user);
          onLoginSuccess();
          onClose();
        } else {
          setError(data.error || "Error al iniciar sesión");
        }
      } else {
        const data = await registerUser(form.username, form.email, form.password);
        if (data.success) {
          const loginData = await loginUser(form.username, form.password);
          if (loginData.success) {
            const user: User = {
              id: loginData.usuario_id,
              nombre: loginData.nombre || form.username,
              email: loginData.email || form.email,
              rol: loginData.rol || "usuario",
            };
            saveUserToStorage(user);
            onLoginSuccess();
            onClose();
          } else {
            setIsLogin(true);
            setError("");
          }
        } else {
          setError(data.error || "Error al registrar");
        }
      }
    } catch (err: unknown) {
      const axios = await import("axios");
      if (axios.default.isAxiosError(err) && err.response?.data?.error) {
        setError(err.response.data.error);
      } else if (err instanceof Error) {
        setError(`Error de conexión: ${err.message}`);
      } else {
        setError("Error de conexión");
      }
    } finally {
      setLoading(false);
    }
  };

  const iconInputClass =
    "mt-1.5 flex items-center gap-2 rounded-xl border border-white/10 bg-[#0b0d0f] px-3 transition focus-within:border-amber-500 focus-within:ring-2 focus-within:ring-amber-500/10";

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-sm rounded-2xl border border-white/10 bg-[#15181d] p-6 shadow-2xl shadow-black/40"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          aria-label="Cerrar"
          className="absolute right-4 top-4 rounded-lg p-1 text-slate-500 transition hover:bg-white/5 hover:text-white"
          onClick={onClose}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M4 4l8 8M12 4l-8 8" />
          </svg>
        </button>

        <h2 className="font-display text-xl font-bold text-white">
          {isLogin ? "Bienvenido de vuelta" : "Crea tu cuenta"}
        </h2>
        <p className="mt-1 text-sm text-slate-400">
          {isLogin
            ? "Ingresa tus credenciales para continuar."
            : "Regístrate para acceder al catálogo completo."}
        </p>

        <div className="mt-5 flex rounded-xl bg-white/[0.04] p-1">
          <button
            type="button"
            onClick={() => { setIsLogin(true); setError(""); resetForm(); }}
            className={`flex-1 rounded-lg py-2 text-sm font-medium transition ${
              isLogin
                ? "bg-amber-500/15 text-amber-300"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Iniciar sesión
          </button>
          <button
            type="button"
            onClick={() => { setIsLogin(false); setError(""); resetForm(); }}
            className={`flex-1 rounded-lg py-2 text-sm font-medium transition ${
              !isLogin
                ? "bg-amber-500/15 text-amber-300"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Registrarse
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-5 flex flex-col gap-3">
          {isLogin ? (
            <>
              <label className="text-xs font-medium text-slate-400">
                Correo o usuario
                <div className={iconInputClass}>
                  <FaEnvelope className="shrink-0 text-slate-500" size={14} />
                  <input
                    name="identifier"
                    type="text"
                    placeholder="tu@email.com"
                    value={form.identifier}
                    onChange={handleChange}
                    className="w-full bg-transparent py-2.5 text-sm text-white outline-none placeholder:text-slate-600"
                    required
                  />
                </div>
              </label>
              <label className="text-xs font-medium text-slate-400">
                Contraseña
                <div className={iconInputClass}>
                  <FaLock className="shrink-0 text-slate-500" size={14} />
                  <input
                    name="password"
                    type="password"
                    placeholder="Contraseña"
                    value={form.password}
                    onChange={handleChange}
                    className="w-full bg-transparent py-2.5 text-sm text-white outline-none placeholder:text-slate-600"
                    required
                  />
                </div>
              </label>
            </>
          ) : (
            <>
              <label className="text-xs font-medium text-slate-400">
                Nombre de usuario
                <div className={iconInputClass}>
                  <FaUser className="shrink-0 text-slate-500" size={14} />
                  <input
                    name="username"
                    type="text"
                    placeholder="Usuario"
                    value={form.username}
                    onChange={handleChange}
                    className="w-full bg-transparent py-2.5 text-sm text-white outline-none placeholder:text-slate-600"
                    required
                  />
                </div>
              </label>
              <label className="text-xs font-medium text-slate-400">
                Correo electrónico
                <div className={iconInputClass}>
                  <FaEnvelope className="shrink-0 text-slate-500" size={14} />
                  <input
                    name="email"
                    type="email"
                    placeholder="tu@email.com"
                    value={form.email}
                    onChange={handleChange}
                    className="w-full bg-transparent py-2.5 text-sm text-white outline-none placeholder:text-slate-600"
                    required
                  />
                </div>
              </label>
              <label className="text-xs font-medium text-slate-400">
                Contraseña
                <div className={iconInputClass}>
                  <FaLock className="shrink-0 text-slate-500" size={14} />
                  <input
                    name="password"
                    type="password"
                    placeholder="Contraseña"
                    value={form.password}
                    onChange={handleChange}
                    className="w-full bg-transparent py-2.5 text-sm text-white outline-none placeholder:text-slate-600"
                    required
                  />
                </div>
              </label>
            </>
          )}
          {error && (
            <p role="alert" className="rounded-lg border border-red-500/20 bg-red-950/20 px-3 py-2 text-sm text-red-300">
              {error}
            </p>
          )}
          <button
            type="submit"
            disabled={loading}
            className="mt-1 rounded-xl bg-amber-500 py-2.5 text-sm font-semibold text-[#19140a] transition hover:bg-amber-400 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? "Cargando…" : isLogin ? "Iniciar sesión" : "Crear cuenta"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default AuthModal;
