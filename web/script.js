const initData = window.Telegram.WebApp.initData;

fetch("https://cardspb4.ru/api/init", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ initData })
})
.then(res => res.json())
.then(data => {
  log("📥 Ответ от сервера:");
  log(JSON.stringify(data, null, 2));

  document.body.innerHTML += `
    <h2>Привет, ${data.first_name || data.username || "гость"}!</h2>
    <p>Ваш Telegram ID: ${data.telegram_id}</p>
  `;
})
.catch(err => {
  log("❌ Ошибка при запросе:");
  log(err.message);
});
