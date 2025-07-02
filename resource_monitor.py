import psutil
import time
import csv
import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
import matplotlib.pyplot as plt
import pandas as pd
import tkinter as tk
from tkinter import ttk

# Email configuration (replace with your details)
EMAIL_ADDRESS = "your_email@gmail.com"  # Replace with your Gmail address
EMAIL_PASSWORD = "your_app_password"    # Replace with your App Password
TO_EMAIL = "recipient_email@example.com"  # Replace with the recipient's email
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Counter for consecutive high usage
high_usage_counts = {"cpu": 0, "ram": 0, "disk": 0}

def send_email(subject, body):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = TO_EMAIL

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, TO_EMAIL, msg.as_string())
        print(f"Email sent: {subject}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def get_system_stats():
    cpu_usage = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    ram_usage = ram.percent
    disk = psutil.disk_usage('/')
    disk_usage = disk.percent
    network = psutil.net_io_counters()
    bytes_sent = network.bytes_sent
    bytes_received = network.bytes_recv
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return {
        "timestamp": timestamp,
        "cpu_usage": cpu_usage,
        "ram_usage": ram_usage,
        "disk_usage": disk_usage,
        "bytes_sent": bytes_sent,
        "bytes_received": bytes_received
    }

def log_to_csv(stats):
    filename = "system_stats.csv"
    write_headers = not os.path.exists(filename)
    
    with open(filename, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=["timestamp", "cpu_usage", "ram_usage", "disk_usage", "bytes_sent", "bytes_received"])
        if write_headers:
            writer.writeheader()
        writer.writerow(stats)

def plot_system_usage():
    try:
        data = pd.read_csv("system_stats.csv")
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        
        plt.figure(figsize=(10, 6))
        plt.plot(data['timestamp'], data['cpu_usage'], label='CPU Usage (%)', color='blue', linewidth=2)
        plt.plot(data['timestamp'], data['ram_usage'], label='RAM Usage (%)', color='green', linewidth=2)
        plt.plot(data['timestamp'], data['disk_usage'], label='Disk Usage (%)', color='red', linewidth=2)
        
        plt.xlabel('Time')
        plt.ylabel('Usage (%)')
        plt.title('System Resource Usage Over Time')
        plt.legend()
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"Failed to plot data: {e}")

class SystemMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("System Resource Monitor")
        self.root.geometry("500x400")
        self.root.configure(bg="#f0f0f0")
        
        # Styling
        self.style = ttk.Style()
        self.style.configure("TLabel", font=("Arial", 12), background="#f0f0f0")
        self.style.configure("TButton", font=("Arial", 12))
        self.style.configure("TProgressbar", thickness=20)
        
        # Title
        ttk.Label(root, text="System Resource Monitor", font=("Arial", 16, "bold"), background="#f0f0f0").pack(pady=10)
        
        # Progress bars and labels
        self.cpu_label = ttk.Label(root, text="CPU Usage: 0.0%")
        self.cpu_label.pack(pady=5)
        self.cpu_progress = ttk.Progressbar(root, length=400, mode='determinate')
        self.cpu_progress.pack(pady=5)
        
        self.ram_label = ttk.Label(root, text="RAM Usage: 0.0%")
        self.ram_label.pack(pady=5)
        self.ram_progress = ttk.Progressbar(root, length=400, mode='determinate')
        self.ram_progress.pack(pady=5)
        
        self.disk_label = ttk.Label(root, text="Disk Usage: 0.0%")
        self.disk_label.pack(pady=5)
        self.disk_progress = ttk.Progressbar(root, length=400, mode='determinate')
        self.disk_progress.pack(pady=5)
        
        self.network_label = ttk.Label(root, text="Network: Sent 0 bytes, Received 0 bytes")
        self.network_label.pack(pady=5)
        
        self.status_label = ttk.Label(root, text="Status: Monitoring...", foreground="black")
        self.status_label.pack(pady=10)
        
        # Stop button
        ttk.Button(root, text="Stop Monitoring", command=self.stop_monitoring).pack(pady=10)
        
        # Start monitoring
        self.running = True
        self.update_stats()
    
    def update_stats(self):
        if not self.running:
            return
        
        stats = get_system_stats()
        
        # Update GUI
        self.cpu_label.config(text=f"CPU Usage: {stats['cpu_usage']}%")
        self.cpu_progress['value'] = stats['cpu_usage']
        
        self.ram_label.config(text=f"RAM Usage: {stats['ram_usage']}%")
        self.ram_progress['value'] = stats['ram_usage']
        
        self.disk_label.config(text=f"Disk Usage: {stats['disk_usage']}%")
        self.disk_progress['value'] = stats['disk_usage']
        
        self.network_label.config(text=f"Network: Sent {stats['bytes_sent']} bytes, Received {stats['bytes_received']} bytes")
        
        # Check alerts
        alerts = []
        global high_usage_counts
        
        if stats["cpu_usage"] > 80:
            high_usage_counts["cpu"] += 1
            alerts.append(f"High CPU usage! {stats['cpu_usage']}%")
            if high_usage_counts["cpu"] >= 3:
                send_email("System Monitor Alert: High CPU Usage", 
                          f"CPU usage has been above 80% for 3 checks: {stats['cpu_usage']}% at {stats['timestamp']}")
                high_usage_counts["cpu"] = 0
        else:
            high_usage_counts["cpu"] = 0
        
        if stats["ram_usage"] > 80:
            high_usage_counts["ram"] += 1
            alerts.append(f"High RAM usage! {stats['ram_usage']}%")
            if high_usage_counts["ram"] >= 3:
                send_email("System Monitor Alert: High RAM Usage", 
                          f"RAM usage has been above 80% for 3 checks: {stats['ram_usage']}% at {stats['timestamp']}")
                high_usage_counts["ram"] = 0
        else:
            high_usage_counts["ram"] = 0
        
        if stats["disk_usage"] > 80:
            high_usage_counts["disk"] += 1
            alerts.append(f"High Disk usage! {stats['disk_usage']}%")
            if high_usage_counts["disk"] >= 3:
                send_email("System Monitor Alert: High Disk Usage", 
                          f"Disk usage has been above 80% for 3 checks: {stats['disk_usage']}% at {stats['timestamp']}")
                high_usage_counts["disk"] = 0
        else:
            high_usage_counts["disk"] = 0
        
        # Update status label
        if alerts:
            self.status_label.config(text="Status: " + "; ".join(alerts), foreground="red")
        else:
            self.status_label.config(text="Status: Monitoring...", foreground="black")
        
        # Log to CSV
        log_to_csv(stats)
        
        # Schedule next update
        self.root.after(5000, self.update_stats)
    
    def stop_monitoring(self):
        self.running = False
        self.root.destroy()
        plot_system_usage()

def main():
    root = tk.Tk()
    app = SystemMonitorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.stop_monitoring)  # Handle window close
    root.mainloop()

if __name__ == "__main__":
    main()