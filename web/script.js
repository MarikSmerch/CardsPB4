if (window.Telegram && window.Telegram.WebApp) {
    const tg = window.Telegram.WebApp;
    tg.ready(); // важно: Telegram начинает инициализацию WebApp

    tg.expand(); // откроет WebApp в полный размер

    document.body.innerHTML += `<p>✅ WebApp активен для ${tg.initDataUnsafe.user?.username || 'неизвестного юзера'}</p>`;
} else {
    document.body.innerHTML += "<p>❗ Telegram.WebApp не найден</p>";
}
