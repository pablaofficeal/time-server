        let allData = [];
        
        // Загружаем данные при старте
        fetch('/api/data')
            .then(response => response.json())
            .then(data => {
                allData = data;
                updateStats(data);
            });

        // Фильтрация данных
        function filterData(days) {
            document.querySelectorAll('.btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            const now = new Date();
            const filteredData = days === 0 
                ? allData 
                : allData.filter(item => {
                    const itemDate = new Date(item.start_time);
                    const diffDays = (now - itemDate) / (1000 * 60 * 60 * 24);
                    return diffDays <= days;
                });
            
            updateStats(filteredData);
            document.getElementById('timeChart').src = `/api/plot?range=${days}&t=${new Date().getTime()}`;
        }

        // Обновление статистики
        function updateStats(data) {
            if (data.length === 0) return;
            
            // Общее время (часы)
            const totalHours = (data.reduce((sum, item) => sum + item.duration, 0) / 3600).toFixed(1);
            document.getElementById('totalHours').textContent = `${totalHours} ч`;
            
            // Топ программа
            const apps = {};
            data.forEach(item => {
                apps[item.app_name] = (apps[item.app_name] || 0) + item.duration;
            });
            const topApp = Object.entries(apps).sort((a, b) => b[1] - a[1])[0];
            document.getElementById('topApp').textContent = `${topApp[0]} (${(topApp[1]/3600).toFixed(1)}ч)`;

            // Топ программа на 2 месце
            const topApp2 = Object.entries(apps).sort((a, b) => b[1] - a[1])[1];
            document.getElementById('topApp2').textContent = `${topApp2[0]} (${(topApp2[1]/3600).toFixed(1)}ч)`;

            // Топ 5 программ за 1 месец
            const topApps = Object.entries(apps).sort((a, b) => b[1] - a[1]);
            document.getElementById('topApp1').textContent = `${topApps[0][0]} (${(topApps[0][1]/3600).toFixed(1)}ч)`;
            document.getElementById('topApp12').textContent = `${topApps[1][0]} (${(topApps[1][1]/3600).toFixed(1)}ч)`;
            document.getElementById('topApp3').textContent = `${topApps[2][0]} (${(topApps[2][1]/3600).toFixed(1)}ч)`;
            document.getElementById('topApp4').textContent = `${topApps[3][0]} (${(topApps[3][1]/3600).toFixed(1)}ч)`;
            document.getElementById('topApp5').textContent = `${topApps[4][0]} (${(topApps[4][1]/3600).toFixed(1)}ч)`;
            
            // Генерируем график программ (заглушка - можно доработать)
            document.getElementById('appsChart').src = `/api/apps_plot?t=${new Date().getTime()}`;
            // Здесь можно добавить логику для генерации графика программ
            // Например, можно использовать библиотеку Chart.js или другую для визуализации данных
            // Пример: new Chart(ctx, { type: 'bar', data: {...}, options: {...} });
            // Или просто обновить src изображения с графиком
            // document.getElementById('appsChart').src = `/api/apps_plot?data=${encodeURIComponent(JSON.stringify(apps))}`;

document.getElementById('openTopApps').addEventListener('click', () => {
    const topApps = document.getElementById('top-apps');
    
    // Если элемент скрыт — показываем, если видим — скрываем
    if (topApps.style.display === 'none' || topApps.style.display === '') {
        topApps.style.display = 'block';
        topApps.style.top = `${document.getElementById('openTopApps').offsetTop}px`;
        topApps.style.left = `${document.getElementById('openTopApps').offsetLeft}px`;
    } else {
        topApps.style.display = 'none';  // Скрываем
    }
});

}
    // Получение данных о пользователях онлайн
    fetch('/api/online')
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка сервера: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
            const onlineUsers = document.getElementById('onlineUsers');
            
            // Очищаем текущий список
            onlineUsers.innerHTML = '';

            // Проверяем, есть ли ошибка в ответе
            if (data.error) {
                const listItem = document.createElement('li');
                listItem.textContent = data.error;
                onlineUsers.appendChild(listItem);
                return;
            }

            // Если user_name нет, показываем количество пользователей
            const listItem = document.createElement('li');
            listItem.textContent = `Пользователей онлайн: ${data.online_users}`;
            onlineUsers.appendChild(listItem);
        })
        .catch(error => {
            console.error('Ошибка при загрузке данных:', error);
            const onlineUsers = document.getElementById('onlineUsers');
            onlineUsers.innerHTML = '';
            const listItem = document.createElement('li');
            listItem.textContent = 'Ошибка загрузки данных';
            onlineUsers.appendChild(listItem);
        });

        document.getElementById('openTimeChart').addEventListener('click', function() {
            window.open('/api/plot?range=1', '_blank');
        })

        document.getElementById('openTimeChart2').addEventListener('click', function() {
            window.open('/api/apps_plot?range=1', '_blank');
        })