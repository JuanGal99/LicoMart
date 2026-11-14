import type { ReactNode } from "react";

type LoginButtonProps = {
  onClick?: () => void;
  label?: string;
  icon?: ReactNode;
};

const LoginButton: React.FC<LoginButtonProps> = ({
  onClick,
  label = "Iniciar Sesión",
  icon,
}) => {
  return (
    <button
      type="button"
      onClick={onClick}
      className="text-white border border-white/20 flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-white/10 transition cursor-pointer"
    >
      {icon}
      <span className="text-sm font-medium">{label}</span>
    </button>
  );
};

export default LoginButton;
