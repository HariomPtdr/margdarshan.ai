import { Languages } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

const LANGS = [
  { code: "hi", label: "हिंदी", short: "हिं" },
  { code: "en", label: "English", short: "EN" },
  { code: "hinglish", label: "Hinglish", short: "HG" },
];

export function LanguageSwitcher() {
  const { i18n } = useTranslation();
  const [open, setOpen] = useState(false);

  const current = LANGS.find((l) => l.code === i18n.language) || LANGS[2];

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 bg-white px-3 py-1.5 rounded-full text-sm font-semibold text-gray-800 hover:bg-gray-50 shadow-sm border border-gray-200"
      >
        <Languages size={16} />
        <span>{current.short}</span>
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-44 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
          {LANGS.map((lang) => (
            <button
              key={lang.code}
              onClick={() => {
                i18n.changeLanguage(lang.code);
                setOpen(false);
              }}
              className={`w-full text-left px-4 py-3 text-sm hover:bg-gray-50 first:rounded-t-lg last:rounded-b-lg ${
                lang.code === i18n.language ? "bg-saffron/10 font-semibold" : ""
              }`}
            >
              {lang.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
