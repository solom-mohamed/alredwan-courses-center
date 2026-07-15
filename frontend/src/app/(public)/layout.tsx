import Footer from "@/components/layout/landing/Footer";
import MobileNavBar from "@/components/layout/landing/MobileNavBar";
import NavBar from "@/components/layout/landing/NavBar";

export const dynamic = "force-dynamic";
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="tablet:grid-rows-[1fr_auto_auto] grid grid-rows-[auto_1fr_auto]">
      <NavBar />
      {children}
      <Footer />
      <MobileNavBar />
    </div>
  );
}
