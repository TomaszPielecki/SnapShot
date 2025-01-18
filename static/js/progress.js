document.addEventListener("DOMContentLoaded", function() {
    const progressBar = document.getElementById("progress-bar");
    const eventSource = new EventSource("/screenshots");

    eventSource.onmessage = function(event) {
        const progress = event.data;
        progressBar.style.width = progress + "%";
        progressBar.innerText = progress + "%";
        if (progress >= 100) {
            eventSource.close();
        }
    };
});