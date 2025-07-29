function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

// Общая настройка jQuery AJAX
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        // Добавляем CSRF только если метод изменяет данные и запрос к своему домену
        if (!(/^GET|HEAD|OPTIONS|TRACE$/i.test(settings.type)) && !this.crossDomain) {
            xhr.setRequestHeader('X-CSRFToken', csrftoken);
        }
    }
});
