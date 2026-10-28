const PORTS = [9981, 9982, 9983, 9984];

async function checkStatus() {
  const textElem = document.getElementById("status-text");
  const indElem = document.getElementById("status-ind");

  textElem.textContent = "Checking...";
  indElem.className = "indicator";

  for (const port of PORTS) {
    try {
      const res = await fetch(`http://127.0.0.1:${port}/status`, { cache: "no-store" });
      if (res.ok) {
        const data = await res.json();
        indElem.className = "indicator online";
        textElem.innerHTML = `<span class="indicator online"></span> Online (${data.blender_version || 'Blender 5.0'}) [Port ${port}]`;
        return;
      }
    } catch (err) {}
  }

  indElem.className = "indicator offline";
  textElem.innerHTML = `<span class="indicator offline"></span> Offline (Not running)`;
}

document.getElementById("btn-check").addEventListener("click", checkStatus);
document.addEventListener("DOMContentLoaded", checkStatus);
