import { useState } from "react";
import {
  registerUser,
  loginUser,
  saveUserToStorage,
  type User,
} from "../services/auth";
import { FaEnvelope, FaLock } from "react-icons/fa"; // usando react-icons

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

  if (!visible) return null;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
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
        const data = await registerUser(
          form.username,
          form.email,
          form.password
        );
        if (data.success) {
          setIsLogin(true);
          setError("");
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
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50">
      <div className="bg-[#1A1D21] p-6 rounded-xl w-full max-w-sm relative shadow-lg">
        <button
          className="absolute top-2 right-2 text-gray-400 hover:text-white"
          onClick={onClose}
        >
          ✕
        </button>

        {/* Encabezado */}
        <h2 className="text-white font-semibold text-lg mb-1">
          Accede a tu cuenta
        </h2>
        <p className="text-[#94A3B8] text-sm mb-3">
          Inicia sesión en tu cuenta existente o crea una nueva cuenta para
          acceder a todas las funcionalidades
        </p>

        {/* Botones login/registro estilo toggle */}
        <div className="flex bg-[#2A2D31] rounded-lg p-1 mb-4">
          <button
            onClick={() => { setIsLogin(true); setError(""); setForm({ identifier: "", password: "", username: "", email: "" }); }}
            className={`flex-1 py-2 rounded-md transition ${
              isLogin
                ? "bg-[#1A1D21] text-white"
                : "bg-transparent text-gray-400 hover:text-white"
            }`}
          >
            Iniciar Sesión
          </button>
          <button
            onClick={() => { setIsLogin(false); setError(""); setForm({ identifier: "", password: "", username: "", email: "" }); }}
            className={`flex-1 py-2 rounded-md transition ${
              !isLogin
                ? "bg-[#1A1D21] text-white"
                : "bg-transparent text-gray-400 hover:text-white"
            }`}
          >
            Registrarse
          </button>
        </div>

        {/* Formulario */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-1">
          {isLogin ? (
            <>
              <p className="text-white">Correo</p>
              <div className="flex items-center bg-black border border-gray-600 rounded-lg px-2">
                <FaEnvelope className="text-gray-400 w-5 h-5 mr-2" />
                <input
                  name="identifier"
                  type="text"
                  placeholder="tu@email.com"
                  value={form.identifier}
                  onChange={handleChange}
                  className="p-2 w-full bg-transparent text-white focus:outline-none"
                  required
                />
              </div>
              <p className="text-white">Contraseña</p>
              <div className="flex items-center bg-black border border-gray-600 rounded-lg px-2">
                <FaLock className="text-gray-400 w-5 h-5 mr-2" />
                <input
                  name="password"
                  type="password"
                  placeholder="Contraseña"
                  value={form.password}
                  onChange={handleChange}
                  className="p-2 w-full bg-transparent text-white focus:outline-none"
                  required
                />
              </div>
            </>
          ) : (
            <>
              <p className="text-white">Username</p>
              <input
                name="username"
                type="text"
                placeholder="Usuario"
                value={form.username}
                onChange={handleChange}
                className="p-2 rounded-lg bg-black text-white border border-gray-600"
                required
              />
              <p className="text-white">Correo</p>
              <input
                name="email"
                type="email"
                placeholder="Email"
                value={form.email}
                onChange={handleChange}
                className="p-2 rounded-lg bg-black text-white border border-gray-600"
                required
              />
              <p className="text-white">Contraseña</p>
              <input
                name="password"
                type="password"
                placeholder="Contraseña"
                value={form.password}
                onChange={handleChange}
                className="p-2 rounded-lg bg-black text-white border border-gray-600"
                required
              />
            </>
          )}
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <button
            type="submit"
            className="bg-[#2563EB] text-white py-2 rounded-lg font-semibold hover:bg-blue-700"
          >
            {isLogin ? "Iniciar Sesión" : "Registrarse"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default AuthModal;
