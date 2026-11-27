use avic_communication_engine::{ModbusTcpClient, ModbusTcpConfig};
use std::env;
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::{Duration, Instant};

fn arg<T: std::str::FromStr>(args: &[String], index: usize, default: T, name: &str) -> T {
    args.get(index).and_then(|v| v.parse().ok()).unwrap_or_else(|| {
        if args.get(index).is_some() { eprintln!("invalid {name}: {}", args[index]); std::process::exit(2); }
        default
    })
}
fn percentile_ms(samples: &[f64], p: f64) -> f64 {
    if samples.is_empty() { return 0.0; }
    let mut sorted = samples.to_vec();
    sorted.sort_by(|a,b| a.partial_cmp(b).unwrap());
    let idx = ((sorted.len() - 1) as f64 * p).ceil() as usize;
    sorted[idx]
}
fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 || args[1] == "--help" {
        println!("Usage: avic-modbus-bench HOST PORT DEVICES POINTS_PER_DEVICE CYCLES CONCURRENCY");
        return;
    }
    if args.len() != 7 { eprintln!("expected 6 arguments; use --help"); std::process::exit(2); }
    let host = args[1].clone();
    let port: u16 = arg(&args, 2, 502, "port");
    let devices: usize = arg(&args, 3, 100, "devices");
    let points: u16 = arg(&args, 4, 100, "points_per_device");
    let cycles: usize = arg(&args, 5, 10, "cycles");
    let concurrency: usize = arg(&args, 6, 8, "concurrency");
    if devices == 0 || cycles == 0 || concurrency == 0 || points == 0 || points > 125 {
        eprintln!("devices/cycles/concurrency must be positive; points_per_device must be 1..125");
        std::process::exit(2);
    }
    let completed = Arc::new(Mutex::new(0usize));
    let failed = Arc::new(Mutex::new(0usize));
    let latencies = Arc::new(Mutex::new(Vec::<f64>::new()));
    let start = Instant::now();
    let workers = concurrency.min(devices);
    let mut handles = Vec::new();
    for worker in 0..workers {
        let host = host.clone();
        let completed = Arc::clone(&completed);
        let failed = Arc::clone(&failed);
        let latencies = Arc::clone(&latencies);
        handles.push(thread::spawn(move || {
            for device in (worker..devices).step_by(workers) {
                let unit_id = (device % 247 + 1) as u8;
                let config = match ModbusTcpConfig::new(&host, port, unit_id, Duration::from_secs(2)) {
                    Ok(c) => c, Err(e) => { eprintln!("config error: {e}"); *failed.lock().unwrap() += cycles; continue; }
                };
                let mut client = ModbusTcpClient::new(config);
                for _ in 0..cycles {
                    let t = Instant::now();
                    match client.read_holding_registers(0, points) {
                        Ok(values) if values.len() == points as usize => {
                            *completed.lock().unwrap() += values.len();
                            latencies.lock().unwrap().push(t.elapsed().as_secs_f64() * 1000.0);
                        }
                        Ok(_) => *failed.lock().unwrap() += 1,
                        Err(e) => { *failed.lock().unwrap() += 1; eprintln!("device {device}: {e}"); }
                    }
                }
            }
        }));
    }
    for h in handles { if h.join().is_err() { *failed.lock().unwrap() += 1; } }
    let elapsed = start.elapsed().as_secs_f64();
    let done = *completed.lock().unwrap();
    let errors = *failed.lock().unwrap();
    let l = latencies.lock().unwrap();
    println!("engine=rust devices={devices} points_per_device={points} cycles={cycles} concurrency={workers} updates={done} requests={} errors={errors} elapsed_s={elapsed:.6} updates_per_s={:.2} request_p50_ms={:.3} request_p95_ms={:.3} request_p99_ms={:.3}",
        devices * cycles, done as f64 / elapsed, percentile_ms(&l,0.50), percentile_ms(&l,0.95), percentile_ms(&l,0.99));
    if errors > 0 { std::process::exit(1); }
}
