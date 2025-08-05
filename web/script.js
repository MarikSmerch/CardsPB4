console.log("💥 вне load: скрипт работает");

const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  const username = tg.initDataUnsafe?.user?.username || 'неизвестный';
  console.log("✅ Telegram.WebApp активен. Username:", username);
} else {
  console.log("❗ Telegram.WebApp не найден");
}
