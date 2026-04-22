import { Outlet } from "react-router-dom";
import Nav from "./Nav";
import Footer from "./Footer";
import "@/styles/prism.css";

export default function PrismLayout() {
  return (
    <div className="page-fade">
      <Nav />
      <main>
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}
