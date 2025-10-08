const log = (msg) => {
  console.log(msg);
  document.body.insertAdjacentHTML("beforeend", `<p>${msg}</p>`);
};

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
  currentTelegramId = data.telegram_id;
  document.body.innerHTML += `
    <h2>Привет, ${data.first_name || data.username || "гость"}!</h2>
    <p>Ваш Telegram ID: ${data.telegram_id}</p>
  `;
})
.catch(err => {
  log("❌ Ошибка при запросе:");
  log(err.message);
});

let currentTelegramId = null;

function submitCardCode() {
  const code = document.getElementById("cardCodeInput").value.trim();
  const resultField = document.getElementById("activationResult");

  if (!code) {
    resultField.textContent = "Введите код.";
    return;
  }

  if (!currentTelegramId) {
    resultField.textContent = "Telegram ID не определён.";
    return;
  }

  fetch("https://cardspb4.ru/api/activate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, telegram_id: currentTelegramId })
  })
  .then(res => res.json())
  .then(data => {
    resultField.textContent = data.message;
  })
  .catch(err => {
    resultField.textContent = "Ошибка при активации кода.";
    console.error(err);
  });
}