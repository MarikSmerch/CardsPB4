if (window.Telegram && window.Telegram.WebApp) {
    const tg = window.Telegram.WebApp;
    const initData = tg.initData;

    fetch("https://cardspb4.ru/api/init", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ initData })
    })
    .then(res => res.json())
    .then(data => {
        console.log("✅ Авторизован как:", data.username || data.telegram_id);
        window.user = data;
    })
    .catch(err => {
        console.error("❌ Ошибка авторизации:", err);
    });
} else {
    console.warn("❗ Telegram.WebApp не найден — ты открыл страницу вне Telegram");
}
