import React, { useEffect, useMemo, useState } from "react";


// --- Simple in-memory router (no react-router to keep single-file) ---
const PAGES = {
  home:       { title: "Главная" },
  profile:    { title: "Профиль" },
  collection: { title: "Коллекция" },
  about:      { title: "О нас" },
  where:      { title: "Где получить?" },
};

// Utility: Telegram WebApp SDK safe getter
const getTg = () => {
  try { return window?.Telegram?.WebApp ?? null; } catch { return null; }
};

function AnimatedHamburger({ isOpen, setIsOpen, size = 28, color = "#1E0028" }) {
  return (
    <div
      className={`hamburger ${isOpen ? "open" : ""}`}
      style={{ width: size, height: Math.round(size * 0.7) }}
      onClick={() => setIsOpen(!isOpen)}
      role="button"
      aria-label="Открыть меню"
      aria-expanded={isOpen ? "true" : "false"}
      aria-controls="sidebar"
    >
      <span className="hamburger-line line-1" style={{ background: color }} />
      <span className="hamburger-line line-2" style={{ background: color }} />
      <span className="hamburger-line line-3" style={{ background: color }} />
    </div>
  );
}

// --- API helpers ---
async function apiSaveProfile({ first_name, last_name, vk_link }) {
  const tg = getTg();
  const initData = tg?.initData || "";
  const res = await fetch("/api/me", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      initData,
      first_name: first_name ?? null,
      last_name:  last_name  ?? null,
      vk_link:    vk_link    ?? null,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.detail || `Save failed (${res.status})`);
  }
  return res.json();
}

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

  const [debugOpen, setDebugOpen] = useState(false);
  const [initDump, setInitDump] = useState("");

  useEffect(() => {
    const tg = getTg();

    try { tg?.ready?.(); } catch {}

    try {
      tg?.setHeaderColor?.("bg_color");
      tg?.setBackgroundColor?.("#FFFFFF");
    } catch {}

    (async () => {
      try {
        const res = await fetch("/api/init", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ initData: tg?.initData || "" }),
        });
        if (res.ok) setUser(await res.json());
        else throw new Error();
      } catch {
        setError("Не удалось получить данные пользователя");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const CurrentPage = useMemo(() => {
    switch (page) {
      case "home":       return <HomePage user={user} />;
      case "profile":    return <ProfilePage user={user} onSaved={setUser} />;
      case "collection": return <CollectionPage />;
      case "about":      return <AboutPage />;
      case "where":      return <WherePage />;
      default:           return <HomePage user={user} />;
    }
  }, [page, user]);

  // простые встроенные SVG
  const IconMenu = () => (
    <svg width="22" height="16" viewBox="0 0 22 16" fill="none" aria-hidden>
      <rect x="0" y="0" width="22" height="2.5" rx="1.25" fill="#1E0028"/>
      <rect x="0" y="6.75" width="22" height="2.5" rx="1.25" fill="#1E0028"/>
      <rect x="0" y="13.5" width="22" height="2.5" rx="1.25" fill="#1E0028"/>
    </svg>
  );
  const IconX = () => (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path d="M18 6L6 18M6 6l12 12" stroke="#1E0028" strokeWidth="2" strokeLinecap="round"/>
    </svg>
  );

  return (
    <div className="min-h-screen font-unbounded app-minh" style={{ color: "#1E0028" }}>
      {/* Top bar */}
      <div className="sticky top-0 z-40 flex items-center gap-3 px-4 py-3 bg-white/60 backdrop-blur shadow"
          style={{ fontWeight: 500 }}>
        <AnimatedHamburger isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />
        <div className="font-unbounded-medium">
          {page === "home" ? "" : (PAGES[page]?.title || "")}
        </div>
      </div>

        <div className="ml-auto space-x-2">
          <button
            className="px-3 py-1.5 text-xs rounded-xl border border-[#1E0028] hover:bg-white/30"
            onClick={() => {
              const tg = getTg();
              const id = tg?.initData || "";
              setInitDump(id);
              setDebugOpen(true);
              // необязательный эхо-запрос
              fetch("/api/_echo_init", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ initData: id }),
              }).catch(() => {});
            }}
          >
            Показать initData
          </button>
        </div>

      {/* Debug modal */}
      {debugOpen && (
        <div className="fixed inset-0 z-50">
          <div className="absolute inset-0 bg-black/40" onClick={() => setDebugOpen(false)} />
          <div className="absolute left-1/2 top-10 -translate-x-1/2 w-[92%] max-w-2xl bg-white rounded-2xl shadow-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="font-semibold">raw initData</div>
              <div className="space-x-2">
                <button
                  className="px-3 py-1.5 text-xs rounded-xl border border-slate-300 hover:bg-slate-100"
                  onClick={async () => {
                    try {
                      if (navigator.clipboard?.writeText) {
                        await navigator.clipboard.writeText(initDump);
                      } else {
                        const ta = document.createElement('textarea');
                        ta.value = initDump;
                        document.body.appendChild(ta);
                        ta.select();
                        document.execCommand('copy');
                        document.body.removeChild(ta);
                      }
                    } catch {}
                  }}
                >
                  Копировать
                </button>
                <button
                  className="px-3 py-1.5 text-xs rounded-xl border border-slate-300 hover:bg-slate-100"
                  onClick={() => setDebugOpen(false)}
                >
                  Закрыть
                </button>
              </div>
            </div>
            <pre className="max-h-[60vh] overflow-auto text-xs whitespace-pre-wrap break-all border border-slate-200 rounded-xl p-3 bg-slate-50">
              {initDump || "(пусто — открой из Telegram WebApp)"}
            </pre>
          </div>
        </div>
      )}

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

      {/* Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-40"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        id="sidebar"
        className={`sidebar ${sidebarOpen ? "open" : ""}`}   /* <-- классы из CSS */
        role="dialog"
        aria-modal="true"
      >
        {/* Шапка сайдбара — по тапу идём в профиль */}
        <div
          className="p-4 border-b flex items-center gap-3 cursor-pointer"
          onClick={() => { setPage("profile"); setSidebarOpen(false); }}
        >
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

        {/* Пункты меню */}
        <nav className="menu">
          {Object.entries(PAGES).map(([key, meta]) => (
            <button key={key} onClick={() => { setPage(key); setSidebarOpen(false); }}>
              {meta.title}
            </button>
          ))}
        </nav>
      </aside>
    </div>
  );
}

// ---------------- PAGES ----------------
function HomePage({ user }) {
  const [code, setCode] = useState("");
  const [status, setStatus] = useState(null);
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
      setStatus({ type: "err", text: e?.message || "Ошибка при активации" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="baldezh-card">
      {/* Логотип */}
      <div className="full-bleed mt-2 mb-12">
        <img
          className="hero-logo"
          src="/logo-baldezh.png"
          alt="Балдёжный Четвёртый"
        />
      </div>

      {/* Приветствие */}
      <div className="font-unbounded-black leading-tight home-hello">
        привет!
      </div>
      <div className="font-unbounded-black leading-tight home-subtitle">
        введи код карточки:
      </div>

      {/* Поле ввода */}
      <input
        className="code-input font-unbounded-medium home-input"
        value={code}
        onChange={(e) => setCode(e.target.value)}
        placeholder="xxxxx-yyyyy-zzzzz"
        maxLength={17}
      />

      {/* Кнопка */}
      <button
        className="btn-primary font-unbounded-medium home-button"
        onClick={onActivate}
        disabled={loading}
      >
        {loading ? "Ввод…" : "Ввод"}
      </button>

      {/* Описание */}
      <div className="helper font-inter-black-italic home-helper" style={{ opacity: .9 }}>
        данный код находится на карточке<br/>с обратной стороны
        <br/><br/>
        после ввода кода будут добавлены<br/>
        в коллекцию сама карточка и её вариации
        <br/><br/>
        все карточки можно посмотреть<br/>
        в разделе "коллекция"
        <br/><br/>
        собранные карточки можно<br/>
        посмотреть в профиле
      </div>

      {/* Касатка */}
      <div className="flex justify-center home-orca">
        <img src="/logo-orca.png" alt="Касатка" style={{ width: 110, height: "auto" }} />
      </div>

      {/* Статус */}
      {status && (
        <div
          className="mt-4"
          style={{
            color: status.type === "ok" ? "#15803D" : "#B91C1C",
            fontFamily: "'Unbounded', sans-serif",
            fontWeight: 500
          }}
        >
          {status.text}
        </div>
      )}
    </main>
  );
}


function ProfilePage({ user, onSaved }) {
  const [firstName, setFirstName] = useState(user?.first_name || "");
  const [lastName,  setLastName]  = useState(user?.last_name  || "");
  const [vk,        setVk]        = useState(user?.vk_link    || "");
  const [saving,    setSaving]    = useState(false);
  const [msg,       setMsg]       = useState(null); // {type:'ok'|'err', text:''}

  // если user обновился извне — синхронизируем поля формы
  useEffect(() => {
    setFirstName(user?.first_name || "");
    setLastName(user?.last_name || "");
    setVk(user?.vk_link || "");
  }, [user?.first_name, user?.last_name, user?.vk_link]);

  const onSave = async () => {
    setMsg(null);
    // подрезаем пробелы; пустые строки -> null (чтоб на бэке стало NULL)
    const payload = {
      first_name: (firstName || "").trim() || null,
      last_name:  (lastName  || "").trim() || null,
      vk_link:    (vk        || "").trim() || null,
    };
    setSaving(true);
    try {
      const updated = await apiSaveProfile(payload);
      onSaved?.(updated); // обновим пользователя в App
      setMsg({ type: "ok", text: "Сохранено" });
    } catch (e) {
      setMsg({ type: "err", text: e.message || "Не удалось сохранить" });
    } finally {
      setSaving(false);
    }
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
          placeholder="Ссылка на VK (vk.com/..)"
          className="w-full p-3 rounded-2xl border border-slate-300 focus:ring-2 focus:ring-slate-400"
        />
        <button
          onClick={onSave}
          disabled={saving}
          className="px-4 py-3 rounded-2xl bg-slate-900 text-white disabled:opacity-60"
        >
          {saving ? "Сохраняем…" : "Сохранить"}
        </button>
        {msg && (
          <div className={msg.type === "ok" ? "text-green-600" : "text-red-600"}>
            {msg.text}
          </div>
        )}
      </div>

      {/* остальной контент страницы — как у тебя */}
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
