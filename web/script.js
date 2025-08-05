window.addEventListener("load", () => {
  console.log("🧠 Скрипт загружен");

  try {
    const tg = window.Telegram.WebApp;
    tg.ready();
    const username = tg.initDataUnsafe?.user?.username || 'неизвестный';
    console.log("✅ Telegram.WebApp активен. Username:", username);
  } catch (e) {
    console.error("❗ Ошибка в WebApp init:", e);
  }
});
