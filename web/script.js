window.addEventListener("load", () => {
  const debug = document.getElementById("debug");

  alert("🔥 JS работает!");

  const log = (msg) => {
    const p = document.createElement("p");
    p.innerText = msg;
    debug.appendChild(p);
  };

  log("🧠 Скрипт загружен");

  if (window.Telegram && window.Telegram.WebApp) {
    const tg = window.Telegram.WebApp;
    tg.ready();

    const username = tg.initDataUnsafe?.user?.username || 'неизвестный';
    log(`✅ Telegram.WebApp активен. Username: ${username}`);
  } else {
    log("❗ Telegram.WebApp не найден — страница открыта вне Telegram WebView");
  }
});