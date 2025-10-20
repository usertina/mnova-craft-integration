async function loadFiles() {
    let res = await fetch("/api/files");
    let data = await res.json();
    let filesList = document.getElementById("files");
    filesList.innerHTML = "";
    data.files.forEach(f => {
        let li = document.createElement("li");
        li.textContent = f;
        filesList.appendChild(li);
    });
}

async function loadAnalysis() {
    let res = await fetch("/api/analysis");
    let data = await res.json();
    let analysisList = document.getElementById("analysis");
    analysisList.innerHTML = "";
    data.analyses.forEach(f => {
        let li = document.createElement("li");
        li.textContent = f;
        analysisList.appendChild(li);
    });
}

setInterval(() => {
    loadFiles();
    loadAnalysis();
}, 5000);

loadFiles();
loadAnalysis();
