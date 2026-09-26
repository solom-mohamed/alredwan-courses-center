import Image from "next/image";
import { getServerSession } from "next-auth";
import { authConfig } from "@/app/api/auth/[...nextauth]/route";
import Logo from "@/assets/logo.svg";
import LogoutButton from "@/components/auth/LogoutButton";
import { NavBarAuthButtons } from "@/components/layout/landing/NavBarAuthButtons";
import NavLink from "@/components/ui/navigation/NavLink";

export default async function NavBar() {
  const session = await getServerSession(authConfig);

  return (
    <nav className="shadow-soft tablet:hidden desktop-sm:px-80 laptop:px-60 sticky top-0 z-1000 flex h-26 w-full items-center justify-between bg-gray-100/80 px-128 py-3 backdrop-blur-md">
      {session?.user ? (
        <div className="tablet:hidden grid content-center">
          <LogoutButton variant="primary" size="small">
            تسجيل الخروج
          </LogoutButton>
        </div>
      ) : (
        <NavBarAuthButtons />
      )}

      <ul className="text-primary tablet:hidden absolute left-1/2 flex transform-[translateX(-50%)] items-center gap-8 text-[14px]">
        <NavLink variant="landing" href="/#">
          الرئيسية
        </NavLink>
        <NavLink variant="landing" href="/#courses">
          الدورات
        </NavLink>
        <NavLink variant="landing" href="/#about">
          عن الواحة
        </NavLink>
        <NavLink variant="landing" href="/#activities">
          الأنشطة
        </NavLink>
        <NavLink variant="landing" href="/#videos">
          الفيديوهات
        </NavLink>
        <NavLink variant="landing" href="/#contact-us">
          تواصل معنا
        </NavLink>
      </ul>

      <NavLink
        variant="landing"
        href="/"
        className="tablet:mr-auto flex items-center gap-3"
        boldWidth={false}
        canActivate={false}
      >
        <Image alt="Logo" src={Logo} className="h-20" />
      </NavLink>
    </nav>
  );
}
