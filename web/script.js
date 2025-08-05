window.addEventListener("DOMContentLoaded", () => {
    const debug = true;  // Поставь false, если не хочешь видеть отладочную панель

    const output = document.createElement("pre");
    if (debug) {
        output.style.background = "#1e1e1e";
        output.style.color = "#0f0";
        output.style.padding = "10px";
        output.style.fontSize = "13px";
        output.style.marginBottom = "1rem";
        document.body.prepend(output);
    }

    if (window.Telegram && window.Telegram.WebApp) {
        const tg = window.Telegram.WebApp;
        tg.ready(); // Сигнал Telegram'у, что всё загружено
        const initData = tg.initData || tg.initDataUnsafe;

        fetch("https://cardspb4.ru/api/init", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ initData })
        })
        .then(res => res.json())
        .then(data => {
            window.user = data;
            if (debug) {
                output.textContent = `✅ Авторизован как: ${data.username || data.telegram_id}`;
            }
        })
        .catch(err => {
            console.error("❌ Ошибка авторизации:", err);
            if (debug) {
                output.textContent = "❌ Ошибка авторизации:\n" + err;
            }
        });
    } else {
        console.warn("❗ Telegram.WebApp не найден — ты открыл страницу вне Telegram");
        if (debug) {
            output.textContent = "❗ Telegram.WebApp не найден — ты открыл страницу вне Telegram";
        }
    }
});
