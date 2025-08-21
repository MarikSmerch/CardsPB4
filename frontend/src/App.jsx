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

function splitTitle(title) {
  const t = String(title || "");
  if (t.length <= 22) return [t];
  const mid = Math.floor(t.length / 2);
  let idx = t.lastIndexOf(" ", mid);
  if (idx < 10) idx = t.indexOf(" ", mid);
  if (idx <= 0 || idx >= t.length - 3) return [t];
  return [t.slice(0, idx).trim(), t.slice(idx + 1).trim()];
}

function LinedTitle({ title }) {
  return (
    <div className="lined-fullbleed">
      <div className="lined-row">
        <div className="label">{String(title || "").toLowerCase()}</div>
      </div>
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

async function apiCollections() {
  const tg = getTg();
  const initData = tg?.initData || "";
  const res = await fetch("/api/collections", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ initData }),
  });
  if (!res.ok) throw new Error("Collections fetch failed");
  return res.json();
}

async function apiMyCards() {
  const tg = getTg();
  const initData = tg?.initData || "";
  const res = await fetch("/api/me/cards", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ initData }),
  });
  if (!res.ok) throw new Error("Cards fetch failed");
  return res.json();
}

async function apiMyPrizes() {
  const tg = getTg();
  const initData = tg?.initData || "";
  const res = await fetch("/api/me/prizes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ initData }),
  });
  if (!res.ok) throw new Error("Prizes fetch failed");
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
      case "home":       return <HomePage user={user} goTo={(p) => setPage(p)} />;
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
        <div className="font-unbounded-medium"></div>
      </div>

        {/* <div className="ml-auto space-x-2">
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
        </div> */}

      {/* Debug modal */}
      {/* {debugOpen && (
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
      )} */}

      {/* Content */}
      <div className="page-container py-5 max-w-xl mx-auto">
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
          <div className="avatar-sm rounded-full bg-slate-200 overflow-hidden">
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
function HomePage({ user, goTo }) {
  const [code, setCode] = React.useState("");
  const [status, setStatus] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [submitted, setSubmitted] = React.useState(false);

  // 👇 новое: состояние модалки после удачной активации
  const [successModal, setSuccessModal] = React.useState(null);
  // successModal = { first_name, last_name, prizeTitle, isEmptyPrize }

  const toMessage = (e) => {
    if (!e) return "Ошибка";
    if (typeof e === "string") return e;
    if (typeof e?.message === "string") return e.message;
    if (typeof e?.detail === "string") return e.detail;
    try {
      const s = JSON.stringify(e);
      return s && s !== "{}" ? s : "";
    } catch {
      return "";
    }
  };
  const ensureMessage = (val, type) => {
    const s = toMessage(val);
    if (!s || s === "[object Object]") {
      return type === "ok" ? "Готово" : "Произошла ошибка";
    }
    return s;
  };

  const onActivate = async () => {
    if (!code.trim()) {
      setStatus({ type: "err", text: "Введите код" });
      setSubmitted(true);
      return;
    }
    if (!user?.telegram_id) {
      setStatus({ type: "err", text: "Telegram ID не определён" });
      setSubmitted(true);
      return;
    }
    setLoading(true);
    setStatus(null);
    setSubmitted(true);
    try {
      const tg = window?.Telegram?.WebApp;
      const initData = tg?.initData;
      if (!initData) throw new Error("Открой приложение внутри Telegram");

      const res = await apiActivateCode(code.trim(), initData);

      try { sessionStorage.removeItem("collections_v3"); } catch {}

      setStatus({ type: "ok", text: ensureMessage(res?.message || "Готово", "ok") });
      setCode("");

      const fn = res?.card_type?.first_name ?? "";
      const ln = res?.card_type?.last_name ?? "";
      const prizeTitle = res?.prize?.title ?? null;
      const prizeDesc  = res?.prize?.description ?? null;
      setSuccessModal({ first_name: fn, last_name: ln, prizeTitle, prizeDesc });
    } catch (e) {
      setStatus({ type: "err", text: ensureMessage(e, "err") });
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Логотип */}
      <div className="full-bleed mt-2 mb-12">
        <img className="hero-logo" src="/logo-baldezh.png?v=1" alt="Балдёжный Четвёртый" />
      </div>

      <div className="page-container">
        <div className="content-wrap">
          <main className="baldezh-card">
            <div className="font-unbounded-black leading-tight home-hello">привет!</div>
            <div className="font-unbounded-black leading-tight home-subtitle">введи код карточки:</div>

            {/* Поле ввода */}
            <input
              className="code-input font-unbounded-medium home-input"
              value={code}
              onChange={(e) => {
                setCode(e.target.value);
                if (status) setStatus(null);
                if (submitted) setSubmitted(false);
              }}
              placeholder="xxxxx-yyyyy-zzzzz"
              maxLength={17}
            />

            {/* Статус под полем — остаётся */}
            {submitted && (status?.text ?? "") !== "" && (
              <div
                className="status-inline"
                style={{ color: status?.type === "ok" ? "#15803D" : "#B91C1C" }}
              >
                {status.text}
              </div>
            )}

            {/* Кнопка */}
            <button className="btn-primary font-unbounded-medium home-button" onClick={onActivate} disabled={loading}>
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
              <img src="/logo-orca.png?v=1" alt="Касатка" style={{ width: 110, height: "auto" }} />
            </div>
          </main>
        </div>
      </div>

      {/* ✅ Модалка «ура!» */}
      {successModal && (
        <div className="modal-root" onClick={() => setSuccessModal(null)}>
          <div className="modal-backdrop" />

          <div className="modal-wrapper success-wrapper" onClick={(e) => e.stopPropagation()}>
            <div className="success-card">
              <div className="success-title font-unbounded-black">ура!</div>
              <div className="success-sub">добавлена карточка:</div>

              <div className="success-name font-unbounded-black">
                {successModal.first_name || ""}<br/>{successModal.last_name || ""}
              </div>

              <div className="success-prize-text">
                {(!successModal.prizeTitle || successModal.prizeTitle?.toLowerCase() === "ничего")
                  ? (successModal.prizeDesc || "К сожалению, приза не было :(")
                  : (<>
                      <div className="font-unbounded-medium">Ты получил приз!</div>
                      <div>{successModal.prizeDesc || ""}</div>
                    </>)
                }
              </div>

              <div className="success-actions">
                <button
                  className="success-btn secondary"
                  onClick={() => { setSuccessModal(null); goTo?.("collection"); }}
                >
                  в коллекции
                </button>
                <button className="success-btn secondary" onClick={() => setSuccessModal(null)}>
                  назад
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}


function ProfilePage({ user, onSaved }) {
  const [firstName, setFirstName] = React.useState(user?.first_name || "");
  const [lastName,  setLastName]  = React.useState(user?.last_name  || "");
  const [vk,        setVk]        = React.useState(user?.vk_link    || "");
  const [saving,    setSaving]    = React.useState(false);
  const [msg,       setMsg]       = React.useState(null); // {type:'ok'|'err', text:''}

  React.useEffect(() => {
    setFirstName(user?.first_name || "");
    setLastName(user?.last_name || "");
    setVk(user?.vk_link || "");
  }, [user?.first_name, user?.last_name, user?.vk_link]);

  const onSave = async () => {
    setMsg(null);
    const payload = {
      first_name: (firstName || "").trim() || null,
      last_name:  (lastName  || "").trim() || null,
      vk_link:    (vk        || "").trim() || null,
    };
    setSaving(true);
    try {
      const updated = await apiSaveProfile(payload);
      onSaved?.(updated);
      setMsg({ type: "ok", text: "Сохранено" });
    } catch (e) {
      setMsg({ type: "err", text: e.message || "Не удалось сохранить" });
    } finally {
      setSaving(false);
    }
  };

  const [myCards, setMyCards] = React.useState(null);
  const [myPrizes, setMyPrizes] = React.useState(null);

  const [collections, setCollections] = React.useState(null);

  React.useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [cards, prizes] = await Promise.all([apiMyCards(), apiMyPrizes()]);
        if (!alive) return;
        setMyCards(cards || []);
        setMyPrizes(prizes || []);
      } catch {
        if (!alive) return;
        setMyCards([]);
        setMyPrizes([]);
      }
    })();

    (async () => {
      const CACHE_KEY = "collections_v3";
      const cached = sessionStorage.getItem(CACHE_KEY);
      if (cached) {
        try {
          const parsed = JSON.parse(cached);
          if (Date.now() - (parsed.ts || 0) < 5 * 60 * 1000) {
            setCollections(parsed.payload || []);
            return;
          }
        } catch {}
      }
      try {
        const payload = await apiCollections();
        setCollections(payload || []);
        sessionStorage.setItem(CACHE_KEY, JSON.stringify({ ts: Date.now(), payload }));
      } catch {
        setCollections([]);
      }
    })();

    return () => { alive = false; };
  }, []);

  const fizCol = React.useMemo(
    () => (collections || []).find(c => c.slug === "fiz"),
    [collections]
  );

  const fizTypeInfoById = React.useMemo(() => {
    const map = new Map();
    (fizCol?.items || []).forEach(it => {
      const id = it.card_type_id ?? it.id ?? it.card_type?.id;
      if (id != null) {
        map.set(id, {
          image_path: it.image_path,
          description: typeof it.description === "string" ? it.description : "",
          first_name: it.first_name,
          last_name:  it.last_name,
        });
      }
    });
    return map;
  }, [fizCol]);

  const [pModal, setPModal] = React.useState(null); // {img, first_name, last_name, description, code}

  const openMyCardModal = (card) => {
    const info = fizTypeInfoById.get(card?.card_type?.id) || {};
    setPModal({
      img: info.image_path,
      first_name: info.first_name ?? card?.card_type?.first_name ?? "",
      last_name:  info.last_name  ?? card?.card_type?.last_name  ?? "",
      description: info.description || "",
      code: card?.code || "",
    });
  };

  return (
    <div className="profile-wrap">
      <h1 className="profile-title">Мой профиль</h1>

      {/* Аватар и username */}
      <div className="profile-header">
        <div className="avatar-lg">
          {user?.avatar_url ? (
            <img src={`${user.avatar_url}${user.avatar_url.includes('?') ? '&' : '?'}v=1`} alt="avatar" className="w-full h-full object-cover" />
          ) : <div className="avatar-placeholder" />}
        </div>
        <div className="profile-username">@{user?.username || "unknown"}</div>
      </div>

      <div className="divider" />

      {/* Форма редактирования */}
      <div className="profile-form">
        <label className="field">
          <span>Имя</span>
          <input
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            placeholder="Имя"
            className="profile-input"
          />
        </label>
        <label className="field">
          <span>Фамилия</span>
          <input
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            placeholder="Фамилия"
            className="profile-input"
          />
        </label>
        <label className="field">
          <span>Ссылка на VK (опционально)</span>
          <input
            value={vk}
            onChange={(e) => setVk(e.target.value)}
            placeholder="https://vk.com/username"
            className="profile-input"
          />
        </label>

        <div className="profile-actions">
          <button onClick={onSave} disabled={saving} className="btn-save">
            {saving ? "Сохраняем…" : "Сохранить"}
          </button>
          {msg && (
            <div className={`save-msg ${msg.type === "ok" ? "ok" : "err"}`}>
              {msg.text}
            </div>
          )}
        </div>
      </div>

      <div className="divider" />

      {/* Мои карточки */}
      <h2 className="profile-subtitle">Мои карточки</h2>
      {myCards === null ? (
        <div className="muted">Загрузка…</div>
      ) : myCards.length === 0 ? (
        <div className="muted">Ты еще не активировал карточки :(</div>
      ) : (
        <div className="cards-grid mycards-grid">
          {myCards.map((c) => {
            const info = fizTypeInfoById.get(c?.card_type?.id) || {};
            const img = info.image_path;
            const title = `${info.first_name ?? c?.card_type?.first_name ?? ""} ${info.last_name ?? c?.card_type?.last_name ?? ""}`.trim();
            return img ? (
              <button
                key={c.code}
                className="card-thumb"
                onClick={() => openMyCardModal(c)}
              >
                <img
                  src={`${img}${img.includes('?') ? '&' : '?'}v=1`}
                  alt={title || "карточка"}
                  loading="lazy"
                />
              </button>
            ) : (
              <div key={c.code} className="mycard-tile">
                <div className="mycard-name">{title || "карточка"}</div>
                <div className="mycard-code">{c.code}</div>
              </div>
            );
          })}
        </div>
      )}

      {/* Модалка для моих карточек */}
      {pModal && (
        <div className="modal-root" onClick={() => setPModal(null)}>
          <div className="modal-backdrop" />
          <div className="modal-wrapper" onClick={(e) => e.stopPropagation()}>
            <div className="modal-card">
              {pModal.img ? (
                <img
                  src={pModal.img}
                  alt={`${pModal.first_name} ${pModal.last_name}`}
                  className="modal-img"
                />
              ) : (
                <div className="modal-info" style={{ padding: 16 }}>
                  нет изображения
                </div>
              )}
            </div>

            <div className="modal-info-panel">
              {/* описание или просто имя/фамилия */}
              {pModal.description
                ? pModal.description.split("\n").map((line, i) => <div key={i}>{line}</div>)
                : <div><b>{pModal.first_name} {pModal.last_name}</b></div>}

              {/* уникальный код */}
              <div style={{ marginTop: 8, opacity: .85 }}>
                <b>Уникальный код:</b> {pModal.code}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="divider" />

      {/* Мои призы */}
      <h2 className="profile-subtitle">Мои призы</h2>
      {myPrizes === null ? (
        <div className="muted">Загрузка…</div>
      ) : myPrizes.length === 0 ? (
        <div className="muted">Ты еще не выиграл призы</div>
      ) : (
        <div className="prizes-list">
          {myPrizes.map((p) => (
            <div key={p.id} className="prize-item">
              • {p.title}{p.count > 1 ? ` ×${p.count}` : ""}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


function CollectionPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [modal, setModal] = useState(null); // {img, name, description}

  // Кэш в sessionStorage
  useEffect(() => {
    const CACHE_KEY = "collections_v3";  // ← новая версия кэша
    const cached = sessionStorage.getItem(CACHE_KEY);
    if (cached) {
      try {
        const parsed = JSON.parse(cached);
        if (Date.now() - (parsed.ts || 0) < 5 * 60 * 1000) {
          // если в кэше вдруг нет description — принудительно перезагружаем
          const hasDesc = (parsed.payload || []).some(col =>
            (col.items || []).some(it => 'description' in it)
          );
          if (hasDesc) {
            setData(parsed.payload);
            setLoading(false);
            return;
          } else {
            sessionStorage.removeItem(CACHE_KEY);
          }
        }
      } catch {}
    }

    (async () => {
      try {
        const payload = await apiCollections();
        const normalized = (payload || []).map(col => ({
          ...col,
          items: (col.items || []).map(it => ({
            ...it,
            description: typeof it.description === "string" ? it.description : ""
          }))
        }));
        setData(normalized);
        sessionStorage.setItem(CACHE_KEY, JSON.stringify({ ts: Date.now(), payload: normalized }));
      } catch (e) {
        setErr(e.message || "Не удалось загрузить коллекции");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const fiz = useMemo(() => (data || []).find(c => c.slug === "fiz"), [data]);
  const digital = useMemo(() => (data || []).filter(c => c.slug !== "fiz"), [data]);

  const openModal = (item) => {
    console.log("modal item:", item);
    setModal({
      img: item.image_path,
      first_name: item.first_name,
      last_name: item.last_name,
      description: item.description || "",
    });
  };

const CardsGrid = ({ items }) => {
    return (
      <div className="cards-grid">
        {items.map((it) => (
          <button
            key={`${it.id}-${it.image_path}`}
            className={`card-thumb ${!it.collected ? "inactive" : ""}`}
            onClick={() => openModal(it)}
          >
            <img
              src={`${it.image_path}${it.image_path.includes('?') ? '&' : '?'}v=1`}
              alt={`${it.first_name} ${it.last_name}`}
              loading="lazy"
            />
          </button>
        ))}
      </div>
    );
  };

  if (loading) return <div className="animate-pulse">Загрузка…</div>;
  if (err) return <div className="text-red-600">{err}</div>;
  if (!data) return null;

  return (
    <div className="space-y-10">
      <h1 className="title-h1">коллекция карточек</h1>

      {/* Физические карточки */}
      {fiz && (
        <section className="section">
          <h2 className="section-title">физические карточки</h2>
          <CardsGrid items={fiz.items} />
        </section>
      )}

      {/* Цифровые карточки */}
      <section className="section">
        <h2 className="section-title">цифровые карточки</h2>

        {digital.map((col) => (
          <div key={col.slug} className="section-block">
            <LinedTitle title={col.title} />
            <CardsGrid items={col.items} />
          </div>
        ))}
      </section>

      {/* Модалка с зумом и описанием */}
      {modal && (
        <div className="modal-root" onClick={() => setModal(null)}>
          <div className="modal-backdrop" />

          <div className="modal-wrapper" onClick={(e) => e.stopPropagation()}>
            <div className="modal-card">
              <img
                src={modal.img}
                alt={`${modal.first_name} ${modal.last_name}`}
                className="modal-img"
              />
            </div>

            {modal.description && (
              <div className="modal-info-panel">
                {modal.description.split("\n").map((line, i) => (
                  <div key={i}>{line}</div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}


function AboutPage() {
  const images = useMemo(() => (
    Array.from({ length: 9 }, (_, i) => `/karysel/${i + 1}.jpg?v=1`)
  ), []);

  const [idx, setIdx] = useState(0);
  const clamp = (n) => (n + images.length) % images.length;

  const goPrev = () => setIdx((i) => clamp(i - 1));
  const goNext = () => setIdx((i) => clamp(i + 1));
  const goTo   = (i) => setIdx(clamp(i));

  const [touchX, setTouchX] = useState(null);
  const onTouchStart = (e) => setTouchX(e.touches[0].clientX);
  const onTouchEnd   = (e) => {
    if (touchX == null) return;
    const dx = e.changedTouches[0].clientX - touchX;
    if (Math.abs(dx) > 40) (dx > 0 ? goPrev() : goNext());
    setTouchX(null);
  };

  useEffect(() => {
    const id = setInterval(() => {
      setIdx((i) => clamp(i + 1));
    }, 5000);
    return () => clearInterval(id);
  }, [images.length]);

  return (
    <div className="about-wrap">
      <h1 className="about-title">О нас</h1>

      <div
        className="carousel"
        onTouchStart={onTouchStart}
        onTouchEnd={onTouchEnd}
      >
        <div
          className="carousel-track"
          style={{ transform: `translateX(-${idx * 100}%)` }}
        >
          {images.map((src, i) => (
            <div className="carousel-slide" key={src}>
              <img src={src} alt={`Слайд ${i + 1}`} />
            </div>
          ))}
        </div>
        <button className="carousel-btn prev" onClick={goPrev}>‹</button>
        <button className="carousel-btn next" onClick={goNext}>›</button>
        <div className="carousel-dots">
          {images.map((_, i) => (
            <button
              key={i}
              className={`dot ${i === idx ? "active" : ""}`}
              onClick={() => goTo(i)}
            />
          ))}
        </div>
      </div>

      <div className="about-text">
        <p>
          На связи самое балдёжное профбюро 4 института, и мы знаем,
          как сделать твою студенческую жизнь максимально крутой и
          запоминающейся!
        </p>

        <h3>Мы занимаемся:</h3>
        <ul>
          <li>Организацией крутых мероприятий (Мансарда, Профкарт, Академия Профорка)</li>
          <li>Выездами в лес и коттеджи</li>
          <li>Решением твоих вопросов, помощь в учёбе, защита прав, консультации по студенческим вопросам</li>
        </ul>

        <h3>С нами ты можешь:</h3>
        <ul>
          <li>Найти новых друзей и единомышленников</li>
          <li>Получить нереальные эмоции</li>
          <li>Стать частью дружной и активной команды</li>
          <li>Просто круто провести время</li>
        </ul>

        <p>
          Подписывайся на наши соцсети, чтобы не пропускать балдёжные тусовки!
        </p>
        <p>
          тг: <a href="https://t.me/guap4you" target="_blank">@guap4you</a><br/>
          вк: <a href="https://vk.com/guap4you" target="_blank">vk.com/guap4you</a>
        </p>
      </div>
    </div>
  );
}

function WherePage() {
  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold text-center">
        мероприятия, на которых можно получить карточки
      </h1>

      {/* Полноширинное изображение */}
      <div className="roadmap-wrap">
        <img className="hero-logo" src="/roadmap.png?v=1" alt="Карта мероприятий" />
      </div>
    </div>
  );
}
