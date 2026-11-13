import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Home from "./pages/Home";
import Navbar from "./components/Navbar";
import Admin from "./pages/Admin";
import {
  isLoggedIn,
  getUserFromStorage,
  clearUserFromStorage,
  logoutUser,
  type User,
} from "./services/auth";

function App() {
  const [isLoggedInState, setIsLoggedInState] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    // Verificar si hay un usuario logueado al cargar la app
    if (isLoggedIn()) {
      const savedUser = getUserFromStorage();
      if (savedUser) {
        setUser(savedUser);
        setIsLoggedInState(true);
      }
    }
  }, []);

  const handleLogout = async () => {
    clearUserFromStorage();
    setUser(null);
    setIsLoggedInState(false);
    try {
      await logoutUser();
    } catch (error) {
      console.error("No se pudo cerrar la sesión en el servidor:", error);
    }
  };

  return (
    <BrowserRouter>
      <Navbar
        isLoggedIn={isLoggedInState}
        setIsLoggedIn={setIsLoggedInState}
        user={user}
        setUser={setUser}
        onLogout={handleLogout}
        search={searchQuery}
        setSearch={setSearchQuery}
      />
      <Routes>
        <Route
          path="/"
          element={
            <Home
              isLoggedIn={isLoggedInState}
              user={user}
              search={searchQuery}
              setSearch={setSearchQuery}
            />
          }
        />
        <Route path="/admin" element={
          isLoggedInState && user?.rol === "admin"
            ? <Admin onLogout={handleLogout} />
            : <Navigate to="/" replace />
        } />
        <Route path="*" element={
          <div className="flex min-h-screen flex-col items-center justify-center bg-[#0b0d0f] text-white">
            <h1 className="text-6xl font-bold text-amber-500">404</h1>
            <p className="mt-4 text-lg text-slate-400">Página no encontrada</p>
            <a href="/" className="mt-6 rounded-xl bg-amber-500 px-5 py-2.5 font-semibold text-[#19140a] transition hover:bg-amber-400">Volver al inicio</a>
          </div>
        } />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
