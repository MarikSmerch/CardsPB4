import React, { useEffect, useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, Home, User, Images, Info, MapPin, Gift } from "lucide-react";

// --- Simple in-memory router (no react-router to keep single-file) ---
const PAGES = {
  home: { title: "Главная", icon: Home },
  profile: { title: "Профиль", icon: User },
  collection: { title: "Коллекция", icon: Images },
  about: { title: "О нас", icon: Info },
  where: { title: "Где получить?", icon: MapPin },
};

// Utility: Telegram WebApp SDK safe getter
const getTg = () => {
  try {
    return window?.Telegram?.WebApp ?? null;
  } catch {
    return null;
  }
};

// --- API helpers ---
async function apiInit() {
  const tg = getTg();
  const initData = tg?.initData || "";
  const res = await fetch("/api/init", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ initData }),
  });
  if (!res.ok) throw new Error("Init failed");
  return res.json();
}

async function apiActivateCode(code, initData) {
  const res = await fetch("/api/activate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, initData }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.detail || "Activation request failed");
  }
  return res.json();
}

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [page, setPage] = useState("home");
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const tg = getTg();
    tg?.ready?.();
    (async () => {
      try {
        const data = await apiInit();
        setUser(data);
      } catch (e) {
        setError("Не удалось получить данные пользователя");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const CurrentPage = useMemo(() => {
    switch (page) {
      case "home":
        return <HomePage user={user} />;
      case "profile":
        return <ProfilePage user={user} />;
      case "collection":
        return <CollectionPage />;
      case "about":
        return <AboutPage />;
      case "where":
        return <WherePage />;
      default:
        return <HomePage user={user} />;
    }
  }, [page, user]);

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      {/* Top bar */}
      <div className="sticky top-0 z-40 flex items-center gap-3 px-4 py-3 bg-white/80 backdrop-blur shadow">
        <button
          className="p-2 rounded-xl hover:bg-slate-100 active:scale-95 transition"
          onClick={() => setSidebarOpen(true)}
          aria-label="Открыть меню"
        >
          <Menu className="w-6 h-6" />
        </button>
        <div className="font-semibold">{PAGES[page]?.title || "Карточки"}</div>
        <div className="ml-auto">
          <button
            className="px-3 py-1.5 text-xs rounded-xl border border-slate-300 hover:bg-slate-100"
            onClick={() => {
            // Перезагрузка с ?debug=1 (покажет сырой initData на экране)
            const url = new URL(window.location.href);
            url.searchParams.set("debug", "1");
            window.location.href = url.toString();
          }}
          >
            initData (debug)
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="px-4 py-5 max-w-xl mx-auto">
        {loading ? (
          <div className="animate-pulse">Загрузка…</div>
        ) : error ? (
          <div className="text-red-600">{error}</div>
        ) : (
          CurrentPage
        )}
      </div>

      {/* Sidebar drawer */}
      <AnimatePresence>
        {sidebarOpen && (
          <>
            <motion.div
              className="fixed inset-0 bg-black/40 z-40"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSidebarOpen(false)}
            />
            <motion.aside
              className="fixed left-0 top-0 bottom-0 w-[80%] max-w-[320px] bg-white z-50 shadow-xl"
              initial={{ x: -320 }}
              animate={{ x: 0 }}
              exit={{ x: -320 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
            >
              <div className="p-4 border-b flex items-center gap-3">
                <button
                  className="p-2 rounded-xl hover:bg-slate-100"
                  onClick={() => setSidebarOpen(false)}
                  aria-label="Закрыть меню"
                >
                  <X className="w-6 h-6" />
                </button>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-slate-200 overflow-hidden">
                    {user?.avatar_url ? (
                      <img src={user.avatar_url} alt="avatar" className="w-full h-full object-cover" />
                    ) : null}
                  </div>
                  <div className="leading-tight">
                    <div className="font-semibold">
                      {user?.first_name || user?.username || "Гость"}
                    </div>
                    {user?.last_name ? (
                      <div className="text-slate-500 text-sm">{user.last_name}</div>
                    ) : null}
                  </div>
                </div>
              </div>

              <nav className="p-2">
                {Object.entries(PAGES).map(([key, meta]) => {
                  const Icon = meta.icon;
                  const active = page === key;
                  return (
                    <button
                      key={key}
                      onClick={() => {
                        setPage(key);
                        setSidebarOpen(false);
                      }}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-2xl mb-2 transition ${
                        active ? "bg-slate-900 text-white" : "hover:bg-slate-100"
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                      <span className="text-base font-medium">{meta.title}</span>
                    </button>
                  );
                })}
              </nav>

              <div className="mt-auto p-4 text-xs text-slate-400">
                © {new Date().getFullYear()} CardsPB4
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}

// ---------------- PAGES ----------------
function HomePage({ user }) {
  const [code, setCode] = useState("");
  const [status, setStatus] = useState(null); // {type: 'ok'|'err', text}
  const [loading, setLoading] = useState(false);

  const onActivate = async () => {
    if (!code.trim()) {
      setStatus({ type: "err", text: "Введите код" });
      return;
    }
    if (!user?.telegram_id) {
      setStatus({ type: "err", text: "Telegram ID не определён" });
      return;
    }
    setLoading(true);
    setStatus(null);
    try {
      const tg = window?.Telegram?.WebApp;
      const initData = tg?.initData;
      if (!initData) throw new Error("Открой приложение внутри Telegram");
      const res = await apiActivateCode(code.trim(), initData);
      setStatus({ type: "ok", text: res?.message || "Готово" });
      setCode("");
    } catch (e) {
      setStatus({ type: "err", text: "Ошибка при активации" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold">Активировать код</h1>
      <div className="grid grid-cols-1 gap-3">
        <input
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="xxxxx-yyyyy-zzzzz"
          className="w-full p-3 rounded-2xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-slate-400"
        />
        <button
          onClick={onActivate}
          disabled={loading}
          className="inline-flex items-center justify-center gap-2 px-4 py-3 rounded-2xl bg-slate-900 text-white active:scale-[.99] disabled:opacity-60"
        >
          <Gift className="w-5 h-5" />
          {loading ? "Подтверждаем…" : "Активировать"}
        </button>
        {status && (
          <div className={`${status.type === "ok" ? "text-green-600" : "text-red-600"}`}>
            {status.text}
          </div>
        )}
      </div>
    </div>
  );
}

function ProfilePage({ user }) {
  const [firstName, setFirstName] = useState(user?.first_name || "");
  const [lastName, setLastName] = useState(user?.last_name || "");
  const [vk, setVk] = useState("");

  const onSave = () => {
    // TODO: add POST /api/profile when backend ready
    alert("Сохраним позже API: " + JSON.stringify({ firstName, lastName, vk }));
  };

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold">Профиль</h1>
      <div className="flex items-center gap-4">
        <div className="w-16 h-16 rounded-full bg-slate-200 overflow-hidden">
          {user?.avatar_url ? (
            <img src={user.avatar_url} alt="avatar" className="w-full h-full object-cover" />
          ) : null}
        </div>
        <div className="text-slate-600 text-sm">@{user?.username || "unknown"}</div>
      </div>

      <div className="grid gap-3">
        <input
          value={firstName}
          onChange={(e) => setFirstName(e.target.value)}
          placeholder="Имя"
          className="w-full p-3 rounded-2xl border border-slate-300 focus:ring-2 focus:ring-slate-400"
        />
        <input
          value={lastName}
          onChange={(e) => setLastName(e.target.value)}
          placeholder="Фамилия"
          className="w-full p-3 rounded-2xl border border-slate-300 focus:ring-2 focus:ring-slate-400"
        />
        <input
          value={vk}
          onChange={(e) => setVk(e.target.value)}
          placeholder="Ссылка на VK"
          className="w-full p-3 rounded-2xl border border-slate-300 focus:ring-2 focus:ring-slate-400"
        />
        <button onClick={onSave} className="px-4 py-3 rounded-2xl bg-slate-900 text-white">Сохранить</button>
      </div>

      <section className="pt-6 space-y-3">
        <h2 className="text-xl font-semibold">Моя коллекция</h2>
        <div className="grid grid-cols-3 gap-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="aspect-[3/4] rounded-xl bg-slate-200" />
          ))}
        </div>

        <h2 className="text-xl font-semibold mt-6">Призы</h2>
        <div className="grid grid-cols-2 gap-3">
          {Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="h-24 rounded-xl bg-emerald-100 border border-emerald-300 flex items-center justify-center text-emerald-800">
              Приз #{i + 1}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function CollectionPage() {
  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold">Коллекции</h1>
      <p className="text-slate-600">Здесь будут наборы карточек. Нажимай на коллекцию, чтобы открыть карточки.</p>
      <div className="grid grid-cols-2 gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="rounded-2xl overflow-hidden shadow bg-white">
            <div className="h-28 bg-slate-200" />
            <div className="p-3 font-medium">Коллекция #{i + 1}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function AboutPage() {
  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold">О нас</h1>
      <div className="rounded-2xl overflow-hidden">
        <div className="h-56 bg-slate-300" />
      </div>
      <button className="px-4 py-3 rounded-2xl bg-slate-900 text-white">Кнопка действия</button>
    </div>
  );
}

function WherePage() {
  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold">Где получить?</h1>
      <div className="rounded-2xl overflow-hidden">
        <div className="h-56 bg-slate-300" />
      </div>
      <p className="text-slate-600">Здесь можно разместить карту/фото точек раздачи.</p>
    </div>
  );
}
