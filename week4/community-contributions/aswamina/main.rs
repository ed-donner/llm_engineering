use std::time::Instant;

fn lcg(seed: u64) -> impl Iterator<Item = u64> {
    let mut value = seed;
    std::iter::from_fn(move || {
        value = value.wrapping_mul(1664525).wrapping_add(1013904223) & 0xFFFFFFFF;
        Some(value)
    })
}

fn max_subarray_sum(n: usize, seed: u64, min_val: i64, max_val: i64) -> i64 {
    let range = (max_val - min_val + 1) as u64;
    let mut lcg_gen = lcg(seed);
    let mut random_numbers = Vec::with_capacity(n);
    
    for _ in 0..n {
        let val = (lcg_gen.next().unwrap() % range) as i64 + min_val;
        random_numbers.push(val);
    }
    
    let mut max_sum = i64::MIN;
    
    for i in 0..n {
        let mut current_sum: i64 = 0;
        for j in i..n {
            current_sum += random_numbers[j];
            if current_sum > max_sum {
                max_sum = current_sum;
            }
        }
    }
    
    max_sum
}

fn total_max_subarray_sum(n: usize, initial_seed: u64, min_val: i64, max_val: i64) -> i64 {
    let mut total_sum: i64 = 0;
    let mut lcg_gen = lcg(initial_seed);
    
    for _ in 0..20 {
        let seed = lcg_gen.next().unwrap();
        total_sum += max_subarray_sum(n, seed, min_val, max_val);
    }
    
    total_sum
}

fn main() {
    let n = 10000;
    let initial_seed = 42u64;
    let min_val = -10i64;
    let max_val = 10i64;
    
    let start_time = Instant::now();
    let result = total_max_subarray_sum(n, initial_seed, min_val, max_val);
    let elapsed = start_time.elapsed();
    
    println!("Total Maximum Subarray Sum (20 runs): {}", result);
    println!("Execution Time: {:.6} seconds", elapsed.as_secs_f64());
}