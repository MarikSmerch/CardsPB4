const log = (text) => {
    const p = document.createElement("p");
    p.innerText = text;
    document.body.appendChild(p);
};

if (window.Telegram && window.Telegram.WebApp) {
    const tg = window.Telegram.WebApp;
    log("✅ Telegram.WebApp найден");

    const initData = tg.initData;
    log("initData: " + initData);

    fetch("https://cardspb4.ru/api/init", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ initData })
    })
    .then(res => res.json())
    .then(data => {
        log("✅ Авторизован как: " + (data.username || data.telegram_id));
        window.user = data;
    })
    .catch(err => {
        log("❌ Ошибка авторизации: " + err);
    });

} else {
    log("❗ Telegram.WebApp не найден — ты открыл страницу вне Telegram");
}
