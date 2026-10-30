import { Link } from "react-router-dom";

const Logo: React.FC = () => {
  return (
    <Link
      to="/"
      className="bg-gradient-to-r from-amber-300 to-amber-500 bg-clip-text text-2xl font-bold tracking-tight text-transparent sm:text-3xl"
    >
      LicoMart
    </Link>
  );
};

export default Logo;
