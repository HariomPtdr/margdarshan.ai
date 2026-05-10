import { LogOut, Phone, ShieldCheck, User } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { useAuth } from "../contexts/AuthContext";
import { LanguageSwitcher } from "./LanguageSwitcher";

export function Header() {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);

  return (
    <header className="bg-gradient-to-r from-saffron via-white to-govgreen border-b-2 border-ashok/20">
      <div className="px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-white shadow-sm flex items-center justify-center text-2xl">
            🛡️
          </div>
          <div>
            <h1 className="text-lg md:text-xl font-bold text-gray-900 leading-tight">
              {t("appName")}
            </h1>
            <p className="text-xs text-gray-700 hidden md:block">{t("tagline")}</p>
          </div>
        </div>

        <div className="flex items-center gap-2 md:gap-3">
          <div className="hidden md:flex items-center gap-1 text-xs bg-white/70 px-2 py-1 rounded-full">
            <ShieldCheck size={14} className="text-govgreen" />
            <span className="text-gray-800 font-medium">{t("trustBadge")}</span>
          </div>

          <LanguageSwitcher />

          <a
            href="tel:1234"
            className="flex items-center gap-1 bg-white px-3 py-1.5 rounded-full text-sm font-medium text-ashok hover:bg-gray-50 shadow-sm"
            title={t("header.helpline")}
          >
            <Phone size={14} />
            <span className="hidden sm:inline">1234</span>
          </a>

          <div className="relative">
            <button
              onClick={() => setOpen((o) => !o)}
              className="flex items-center gap-2 bg-ashok/90 text-white pl-1 pr-3 py-1 rounded-full hover:bg-ashok"
            >
              <span className="w-7 h-7 rounded-full bg-white/20 flex items-center justify-center">
                <User size={16} />
              </span>
              <span className="text-sm font-medium hidden sm:inline">
                {user?.name?.split(" ")[0] || "User"}
              </span>
            </button>
            {open && (
              <div className="absolute right-0 top-full mt-2 bg-white border border-gray-200 rounded-lg shadow-lg w-56 z-50">
                <div className="px-3 py-2 border-b border-gray-100">
                  <div className="text-sm font-semibold text-gray-900">{user?.name}</div>
                  <div className="text-xs text-gray-500 truncate">{user?.email}</div>
                  <div className="text-xs text-gray-500">{user?.mobile}</div>
                </div>
                <button
                  onClick={() => {
                    setOpen(false);
                    logout();
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:bg-red-50"
                >
                  <LogOut size={14} /> Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
