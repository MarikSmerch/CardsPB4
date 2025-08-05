window.addEventListener("DOMContentLoaded", () => {
  const log = (msg) => {
    document.body.insertAdjacentHTML("beforeend", `<p>${msg}</p>`);
  };

  log("🧠 Скрипт загружен");

  if (window.Telegram && window.Telegram.WebApp) {
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand(); 
    const username = tg.initDataUnsafe?.user?.username || "гость";
    log(`✅ WebApp активен: ${username}`);
  } else {
    log("❗ Telegram.WebApp не найден — ты открыл страницу вне Telegram");
  }
});
