import { useState } from "react";
import { FaRegUser } from "react-icons/fa";
import { FiLogOut } from "react-icons/fi";
import Logo from "./Logo";
import SearchBar from "./SearchBar";
import CartButton from "./CartButton";
import LoginButton from "./LoginButton";
import AuthModal from "./AuthModal";
import { type User, getUserFromStorage } from "../services/auth";
import { Link, useNavigate } from "react-router-dom";

const Navbar: React.FC<{
  isLoggedIn: boolean;
  setIsLoggedIn: (v: boolean) => void;
  user: User | null;
  setUser: (u: User | null) => void;
  onLogout: () => void;
  search: string;
  setSearch: (v: string) => void;
}> = ({ isLoggedIn, setIsLoggedIn, user, setUser, onLogout, search, setSearch }) => {
  const [showModal, setShowModal] = useState(false);
  const navigate = useNavigate();

  const handleLoginClick = () => {
    if (isLoggedIn) {
      onLogout();
    } else {
      setShowModal(true);
    }
  };

  return (
    <nav className="sticky top-0 z-40 border-b border-white/10 bg-[#101214]/95 px-4 py-3 backdrop-blur-xl">
      <div className="container mx-auto flex flex-wrap items-center justify-between gap-4">
        <Logo />
        <div className="hidden flex-grow justify-center md:flex">
          <SearchBar value={search} onChange={setSearch} className="w-full max-w-md" />
        </div>
        <div className="flex items-center gap-3">
          {isLoggedIn && user?.rol === "admin" && (
            <Link
              to="/admin"
              className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white transition hover:border-amber-500/40 hover:bg-amber-500/10"
            >
              Admin
            </Link>
          )}
          {isLoggedIn && <CartButton />}
          <LoginButton
            onClick={handleLoginClick}
            label={isLoggedIn ? "Cerrar Sesión" : "Iniciar Sesión"}
            icon={
              isLoggedIn ? (
                <FiLogOut className="text-lg" />
              ) : (
                <FaRegUser className="text-lg" />
              )
            }
          />
        </div>
      </div>
      <AuthModal
        visible={showModal}
        onClose={() => setShowModal(false)}
        onLoginSuccess={() => {
          setIsLoggedIn(true);
          const saved = getUserFromStorage();
          if (saved) setUser(saved);
          setShowModal(false);
          if (saved?.rol === "admin") navigate("/admin");
        }}
      />
    </nav>
  );
};

export default Navbar;
