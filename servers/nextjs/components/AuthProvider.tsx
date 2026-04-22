"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // Si ya está en la página de login, no hacer nada
    if (pathname === "/login") {
      return;
    }

    // Verificar si hay token
    const checkAuth = async () => {
      try {
        const response = await fetch("/api/v1/auth/me", {
          credentials: "include",
        });

        if (!response.ok) {
          // No autenticado, redirigir a login
          router.push("/login");
        }
      } catch (error) {
        // Error al verificar, redirigir a login
        router.push("/login");
      }
    };

    checkAuth();
  }, [pathname, router]);

  return <>{children}</>;
}
