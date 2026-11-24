from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
app = Flask(__name__)

# Nilai batas suhu awal (°C)
threshold_suhu = 35.0
sudah_notifikasi = False  # mencegah notifikasi berulang selama suhu masih tinggi
riwayat_suhu = [] #menyimpan list dict {"waktu:..., "temperature":..., "device_id":...}

API_KEY = "iot-rahasia-2310020085"

def cek_api_key():
    key = request.headers.get("X-API-Key")
    if not key or key != API_KEY:
        return jsonify({"error": "API Key tidak valid atau tidak ada"}), 401
    return None


@app.route("/api/threshold", methods=["PUT"])
def set_threshold():
    auth_error = cek_api_key()
    if auth_error:
        return auth_error
    global threshold_suhu, sudah_notifikasi

    data = request.get_json(silent=True) or {}
    if "threshold" not in data:
        return jsonify({"error": "Field 'threshold' wajib diisi"}), 400

    try:
        nilai_baru = float(data["threshold"])
    except (ValueError, TypeError):
        return jsonify({"error": "Field 'threshold' harus berupa angka"}), 400

    threshold_suhu = nilai_baru
    sudah_notifikasi = False  # reset status alert saat batas baru diatur

    return jsonify({
        "status": "ok",
        "message": "Batas suhu berhasil diperbarui",
        "threshold": threshold_suhu
    }), 200


def cek_dan_kirim_notifikasi(suhu, device_id="ESP32-simulator"):
    global sudah_notifikasi

    if suhu > threshold_suhu:
        if not sudah_notifikasi:
            pesan = f"PERINGATAN: Suhu {suhu}°C dari {device_id} melewati batas {threshold_suhu}°C!"
            print(pesan)
            # Tempatkan kode kirim notifikasi eksternal di sini jika diperlukan
            # (misalnya requests.post(webhook_url, json={"text": pesan}))
            sudah_notifikasi = True
    else:
        sudah_notifikasi = False

        def cek_dan_kirim_notifikasi(suhu, device_id="ESP32-simulator"):
            global sudah_notifikasi

            if suhu > threshold_suhu:
                if not sudah_notifikasi:
                    pesan = f"[NOTIFIKASI] suhu {suhu}°C dari {device_id} melewati batas {threshold_suhu}°C!"
                    print(pesan)
                    # Opsional:kirim ke HTTP lain disini
                    sudah_notifikasi = True
            else:
                # reset status jika suhu kembali normal dibawah/sama dengan batas
                sudah_notifikasi = False


@app.route("/api/suhu", methods=["POST"])
def terima_suhu():
    auth_error = cek_api_key()
    if auth_error:
        return auth_error
    data = request.get_json(silent=True) or {}
    if "temperature" not in data:
        return jsonify({"error": "Field 'temperature' wajib diisi"}), 400

    suhu = float(data["temperature"])
    device_id = data.get("device_id", "ESP32-simulator")

    #simpan data suhu ke riwayat untuk grafik Chart.js
    riwayat_suhu.append({
        "waktu": datetime.now().strftime("%H:%M:%S"),
        "device_id": device_id,
        "temperature": suhu,
        "threshold": threshold_suhu
    })
    if len(riwayat_suhu) > 30:
        riwayat_suhu.pop(0)

    cek_dan_kirim_notifikasi(suhu, device_id)

    return jsonify({
        "status": "ok",
        "device_id": device_id,
        "temperature": suhu,
        "threshold": threshold_suhu,
        "alert": suhu > threshold_suhu
    }), 200

@app.route("/api/suhu", methods=["GET"])
def ambil_suhu():
    return jsonify({
        "threshold": threshold_suhu,
        "data": riwayat_suhu
    }), 200

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Dashboard Suhu Real-Time</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body {
      font-family: Arial, sans-serif;
      max-width: 900px;
      margin: 30px auto;
      padding: 0 16px;
      background-color: #f9fafb;
      color: #111827;
    }
    .info {
      margin-bottom: 14px;
      font-size: 16px;
    }
    .card {
      background: #ffffff;
      border: 1px solid #e5e7eb;
      border-radius: 10px;
      padding: 20px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
    }
  </style>
</head>
<body>
  <h2>Monitoring Suhu Real-Time (Chart.js)</h2>
  <div class="info">Batas Suhu Aktif: <strong id="batasText">-</strong> °C</div>
  <div class="card">
    <canvas id="suhuChart" height="110"></canvas>
  </div>

  <script>
    const ctx = document.getElementById("suhuChart").getContext("2d");
    const suhuChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: [],
        datasets: [
          {
            label: "Suhu (°C)",
            data: [],
            borderColor: "rgb(255, 99, 132)",
            backgroundColor: "rgba(255, 99, 132, 0.2)",
            tension: 0.25
          },
          {
            label: "Batas Suhu (°C)",
            data: [],
            borderColor: "rgb(54, 162, 235)",
            borderDash: [6, 6],
            pointRadius: 0
          }
        ]
      },
      options: {
        animation: false,
        scales: {
          y: { beginAtZero: false }
        }
      }
    });

    async function muatData() {
      try {
        const res = await fetch("/api/suhu");
        const json = await res.json();
        document.getElementById("batasText").textContent = json.threshold;

        const items = json.data || [];
        suhuChart.data.labels = items.map(d => d.waktu);
        suhuChart.data.datasets[0].data = items.map(d => d.temperature);
        suhuChart.data.datasets[1].data = items.map(() => json.threshold);
        suhuChart.update();
      } catch (err) {
        console.error("Gagal memuat data:", err);
      }
    }

    muatData();
    setInterval(muatData, 2000);
  </script>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def dashboard():
    return render_template_string(DASHBOARD_HTML)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)