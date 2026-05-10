import "leaflet/dist/leaflet.css";

import L from "leaflet";
import { Crosshair, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { MapContainer, Marker, TileLayer, useMapEvents } from "react-leaflet";
import { useTranslation } from "react-i18next";

// Fix Leaflet default marker icons (Vite doesn't bundle them by path)
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

interface Props {
  open: boolean;
  onClose: () => void;
  onConfirm: (lat: number, lon: number) => void;
}

const DEFAULT_CENTER: [number, number] = [23.2599, 77.4126]; // Bhopal

function ClickableMarker({
  position,
  setPosition,
}: {
  position: [number, number];
  setPosition: (p: [number, number]) => void;
}) {
  useMapEvents({
    click(e) {
      setPosition([e.latlng.lat, e.latlng.lng]);
    },
  });
  return (
    <Marker
      position={position}
      draggable={true}
      eventHandlers={{
        dragend: (e) => {
          const m = e.target as L.Marker;
          const ll = m.getLatLng();
          setPosition([ll.lat, ll.lng]);
        },
      }}
    />
  );
}

export function MapModal({ open, onClose, onConfirm }: Props) {
  const { t } = useTranslation();
  const [pos, setPos] = useState<[number, number]>(DEFAULT_CENTER);
  const [submitting, setSubmitting] = useState(false);
  const mapRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!open) return;
    const timers = [50, 200, 500].map((d) =>
      setTimeout(() => mapRef.current?.invalidateSize(), d),
    );
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (g) => {
          const next: [number, number] = [g.coords.latitude, g.coords.longitude];
          setPos(next);
          mapRef.current?.setView(next, 15);
        },
        () => {},
        { timeout: 4000 },
      );
    }
    return () => timers.forEach(clearTimeout);
  }, [open]);

  if (!open) return null;

  const useGps = () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition((g) => {
      const next: [number, number] = [g.coords.latitude, g.coords.longitude];
      setPos(next);
      mapRef.current?.setView(next, 15);
    });
  };

  const confirm = async () => {
    setSubmitting(true);
    try {
      await onConfirm(pos[0], pos[1]);
      onClose();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-2 md:p-6">
      <div className="bg-white rounded-2xl w-full max-w-2xl h-[85vh] flex flex-col overflow-hidden shadow-2xl">
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
          <div>
            <h3 className="font-bold text-gray-900">{t("map.title")}</h3>
            <p className="text-xs text-gray-500">{t("map.instruction")}</p>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded">
            <X size={22} />
          </button>
        </div>

        <div className="flex-1 relative" style={{ minHeight: "420px" }}>
          <MapContainer
            center={pos}
            zoom={13}
            style={{ position: "absolute", inset: 0, height: "100%", width: "100%" }}
            ref={(m) => {
              if (m) mapRef.current = m;
            }}
          >
            <TileLayer
              url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://osm.org">OpenStreetMap</a>'
              maxZoom={19}
            />
            <ClickableMarker position={pos} setPosition={setPos} />
          </MapContainer>

          <button
            onClick={useGps}
            className="absolute top-3 right-3 z-[400] bg-white rounded-full shadow-lg px-3 py-2 text-sm font-semibold flex items-center gap-1.5 hover:bg-gray-50"
          >
            <Crosshair size={16} />
            {t("map.useGps")}
          </button>
        </div>

        <div className="flex gap-2 p-3 border-t border-gray-200">
          <button
            onClick={onClose}
            className="flex-1 py-3 px-4 rounded-lg border border-gray-300 font-semibold hover:bg-gray-50"
          >
            {t("map.cancel")}
          </button>
          <button
            onClick={confirm}
            disabled={submitting}
            className="flex-1 py-3 px-4 rounded-lg bg-govgreen text-white font-semibold hover:bg-govgreen/90 disabled:opacity-50"
          >
            {submitting ? "..." : t("map.confirm")}
          </button>
        </div>
      </div>
    </div>
  );
}
