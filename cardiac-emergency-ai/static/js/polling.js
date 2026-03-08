document.addEventListener("DOMContentLoaded", function() {
    const container = document.getElementById("status-container");
    if (!container) return;
    
    const patientId = container.getAttribute("data-patient-id");
    if (!patientId) return;
    
    // Single synchronous request instead of polling
    fetch(`/process/${patientId}/`)
        .then(response => response.json())
        .then(data => {
            const statusSpan = document.getElementById("task-status");
            if (data.status === "complete") {
                statusSpan.innerText = "Complete!";
                window.location.href = `/report/${data.report_id}/`;
            } else {
                statusSpan.innerText = "Failed processing.";
            }
        })
        .catch(err => {
            console.error("Processing error:", err);
            document.getElementById("task-status").innerText = "Error during processing.";
        });
});
